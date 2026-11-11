"""Pure transformations: exact dates, no interpolation, auditable joins."""
import numpy as np
import pandas as pd


def validate_prices(frame):
    frame = frame.copy()
    frame.index = pd.to_datetime(frame.index)
    if frame.index.tz is not None:
        frame.index = frame.index.tz_localize(None)
    frame.index = frame.index.normalize()
    if frame.index.duplicated().any():
        raise ValueError('Duplicate price dates')
    frame = frame.sort_index()
    if (frame <= 0).any().any():
        raise ValueError('Nonpositive close price')
    return frame


def returns_from(frame, date):
    """Return percent from an exact baseline; missing baselines remain NaN."""
    date = pd.Timestamp(date)
    base = frame.loc[date] if date in frame.index else pd.Series(np.nan, index=frame.columns)
    return frame.div(base.where(base > 0)).sub(1).mul(100)


def reaction_table(frame, companies, baseline, dates):
    rows = []
    for row in companies.itertuples(index=False):
        target = dates[row.country]
        series = frame[row.ticker] if row.ticker in frame else pd.Series(dtype=float)
        base, close = series.get(pd.Timestamp(baseline), np.nan), series.get(pd.Timestamp(target), np.nan)
        status = 'ok' if pd.notna(base) and pd.notna(close) and base > 0 else 'missing_exact_date'
        rows.append(dict(ticker=row.ticker, company=row.company, country=row.country,
                         baseline_date=baseline, reaction_date=target, baseline_close=base,
                         reaction_close=close, return_pct=(close / base - 1) * 100 if status == 'ok' else np.nan,
                         status=status, include_main=row.include_main))
    return pd.DataFrame(rows)


def match_revenue(revenue, companies):
    if companies.ticker.duplicated().any():
        raise ValueError('Duplicate company ticker')
    matched = revenue.merge(companies[['ticker', 'country']], on='ticker', how='left',
                            validate='many_to_one', indicator=True)
    if (matched['_merge'] != 'both').any():
        raise ValueError('Unmatched revenue ticker')
    if revenue.duplicated(['ticker', 'segment']).any():
        raise ValueError('Duplicate revenue segment')
    return matched.drop(columns='_merge')


def revenue_quality(revenue):
    rows = []
    for ticker, group in revenue.groupby('ticker', sort=False):
        total = group.pct.sum(min_count=1)
        rows.append(dict(ticker=ticker, company=group.company.iloc[0], total_pct=total,
                         delta_from_100=total - 100, negative_count=int((group.pct < 0).sum()),
                         missing_count=int(group.pct.isna().sum()),
                         review_segments=int(group.classification.isin(['mixed', 'needs_review']).sum()),
                         sum_status='within_0.1' if abs(total - 100) <= .100001 else 'review'))
    return pd.DataFrame(rows)
