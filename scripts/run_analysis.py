"""Rebuild the complete local portfolio, using cached source data by default."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
from src.analysis import match_revenue, reaction_table, returns_from, revenue_quality
from src.collect import collect, versions
from src import plots
from src.reporting import write_reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--refresh', action='store_true', help='Download fresh Yahoo data')
    mode.add_argument('--offline', action='store_true', help='Require existing raw caches')
    args = parser.parse_args()
    for folder in ['data/raw', 'data/processed', 'reports/figures']:
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    cfg = json.loads((ROOT / 'configs/analysis.json').read_text(encoding='utf-8'))
    us = pd.read_csv(ROOT / 'data/reference/us_companies.csv')
    kr = pd.read_csv(ROOT / 'data/reference/kr_companies.csv', dtype={'code': str})
    companies = pd.concat([us, kr], ignore_index=True)
    revenue = pd.read_csv(ROOT / 'data/reference/revenue_segments.csv')
    match_revenue(revenue, companies)
    quality = revenue_quality(revenue)
    quality.to_csv(ROOT / 'data/processed/revenue_quality.csv', index=False, encoding='utf-8-sig')
    frames, acquisition = {}, []
    requests = [('oil_long',['BZ=F','CL=F'],'oil_long',cfg['oil_auto_adjust']),
                ('oil_short',['BZ=F','CL=F'],'oil_short',cfg['oil_auto_adjust']),
                ('us_three_dates',us.ticker.tolist(),'us_three_dates',cfg['stock_auto_adjust']),
                ('us_daily',us.ticker.tolist(),'stock_daily',cfg['stock_auto_adjust']),
                ('kr_daily',kr.ticker.tolist(),'stock_daily',cfg['stock_auto_adjust'])]
    for name, tickers, window, adjust in requests:
        print(f'Collecting {name} ({len(tickers)} tickers)', flush=True)
        frames[name], audit = collect(ROOT, name, tickers, cfg['windows'][window], adjust, args.refresh, args.offline)
        acquisition.extend(audit)
    audit = pd.DataFrame(acquisition)
    audit.to_csv(ROOT / 'data/processed/acquisition_manifest.csv', index=False, encoding='utf-8-sig')
    oil_alignment = []
    for name in ['oil_long','oil_short']:
        original = frames[name]
        oil_alignment.append(dict(window=name, union_rows=len(original),
                                  excluded_incomplete_rows=int(original.isna().any(axis=1).sum()),
                                  retained_complete_rows=int(original.notna().all(axis=1).sum())))
        frames[name] = original.dropna(how='any')
    pd.DataFrame(oil_alignment).to_csv(ROOT / 'data/processed/oil_alignment.csv', index=False)
    oil_reactions = []
    for ticker in ['BZ=F','CL=F']:
        series = frames['oil_long'][ticker]
        base = series.get(pd.Timestamp(cfg['baseline_date']), float('nan'))
        after = series.get(pd.Timestamp(cfg['reaction_dates']['US']), float('nan'))
        oil_reactions.append(dict(ticker=ticker, baseline_date=cfg['baseline_date'],
                                  reaction_date=cfg['reaction_dates']['US'],
                                  baseline_close=base, reaction_close=after,
                                  return_pct=(after/base-1)*100 if pd.notna(base) and pd.notna(after) else float('nan')))
    pd.DataFrame(oil_reactions).to_csv(ROOT / 'data/processed/oil_event_reactions.csv', index=False)
    prices = pd.concat([frames['us_daily'],frames['kr_daily']], axis=1).sort_index()
    reactions = reaction_table(prices, companies, cfg['baseline_date'], cfg['reaction_dates'])
    reactions.to_csv(ROOT / 'data/processed/event_reactions.csv', index=False, encoding='utf-8-sig')
    reactions[reactions.include_main].to_csv(ROOT / 'data/processed/event_reactions_main.csv', index=False, encoding='utf-8-sig')
    returns_from(prices, cfg['baseline_date']).to_csv(ROOT / 'data/processed/event_baseline_returns.csv', index_label='Date')
    baselines = []
    for name in ['us_daily','kr_daily']:
        frame = frames[name]
        base = str(frame.dropna(how='all').index.min().date()) if not frame.dropna(how='all').empty else None
        baselines.append(dict(window=name, requested_start=cfg['windows']['stock_daily']['requested_start'],
                              baseline_date=base, rule='first_observed_row_in_market_window_not_event_baseline'))
        returns_from(frame, base).to_csv(ROOT / f'data/processed/{name}_first_observation_returns.csv', index_label='Date')
    pd.DataFrame(baselines).to_csv(ROOT / 'data/processed/daily_baselines.csv', index=False)
    three = frames['us_three_dates'].reindex(pd.to_datetime(cfg['three_dates']))
    three.to_csv(ROOT / 'data/processed/us_three_date_close.csv', index_label='Date')
    # Comparable endpoint changes and their availability, without inference or model fitting.
    industry = reactions.merge(us[['ticker','sub_industry']], on='ticker', how='inner', validate='one_to_one')
    industry[industry.include_main].groupby('sub_industry').agg(
        available_n=('return_pct','count'), mean_return_pct=('return_pct','mean'),
        min_return_pct=('return_pct','min'), max_return_pct=('return_pct','max')
    ).to_csv(ROOT / 'data/processed/us_industry_first_session_summary.csv')
    # Explicit sample sensitivity; inclusion is a post-hoc choice, not an outlier filter.
    sensitivity = []
    for label, subset in [('initial_21', reactions[reactions.country == 'US']),
                          ('main_20_without_TPL', reactions[(reactions.country == 'US') & reactions.include_main])]:
        sensitivity.append(dict(sample=label, n=len(subset), available_n=int(subset.return_pct.notna().sum()),
                                positive_n=int((subset.return_pct > 0).sum()),
                                equal_company_mean_return_pct=subset.return_pct.mean()))
    pd.DataFrame(sensitivity).to_csv(ROOT / 'data/processed/tpl_sample_sensitivity.csv', index=False)
    korean = plots.setup()
    fig_dir = ROOT / 'reports/figures'
    jobs = [
        ('oil_windows.png', lambda p: plots.oil_figure(frames['oil_long'],frames['oil_short'],p)),
        ('event_reactions.png', lambda p: plots.reaction_figure(reactions,p,korean)),
        ('us_industries.png', lambda p: plots.industry_figure(frames['us_daily'],us,cfg['baseline_date'],p)),
        ('hd_hyundai_case.png', lambda p: plots.hd_figure(frames['kr_daily'],revenue,cfg['baseline_date'],p,korean)),
        ('us_initial_21_daily.png', lambda p: plots.grid_figure(frames['us_daily'],us,p,baseline=baselines[0]['baseline_date'])),
        ('us_initial_21_three_dates.png', lambda p: plots.grid_figure(frames['us_three_dates'],us,p,three_dates=cfg['three_dates']))]
    figures = []
    for name, create in jobs:
        print(f'Rendering {name}', flush=True)
        generated = create(fig_dir / name)
        if not generated and (fig_dir / name).exists():
            (fig_dir / name).unlink()
        figures.append(dict(file=name, generated=generated,
                            reason='' if generated else 'Required source or exact baseline data unavailable'))
    hashes = {str(p.relative_to(ROOT)).replace('\\','/'): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in [ROOT / 'configs/analysis.json', *sorted((ROOT / 'data/reference').glob('*.csv'))]}
    failures = audit[(audit.status != 'ok') | audit.error.fillna('').ne('')]
    run = dict(completed_at_utc=datetime.now(timezone.utc).isoformat(), versions=versions(),
               arguments=vars(args), reference_sha256=hashes, figures=figures,
               failed_acquisition_rows=len(failures), missing_reaction_rows=int((reactions.status != 'ok').sum()),
               status='complete' if failures.empty and (reactions.status == 'ok').all() else 'partial')
    (ROOT / 'data/processed/run_manifest.json').write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding='utf-8')
    write_reports(ROOT, cfg, companies, revenue, quality, audit, reactions, frames, run)
    print(f"Run status: {run['status']}; figures: {sum(f['generated'] for f in figures)}/{len(figures)}", flush=True)
    return 0 if run['status'] == 'complete' else 2


if __name__ == '__main__':
    raise SystemExit(main())
