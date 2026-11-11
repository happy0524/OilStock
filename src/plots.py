"""Static report figures with exact date axes and explicit baselines."""
import warnings
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager, dates as mdates
import numpy as np
import pandas as pd
from src.analysis import returns_from

NAVY, BLUE, RED, GRAY = '#172b46', '#147d92', '#c24c42', '#788797'
PALETTE = ['#147d92', '#c24c42', '#ae7e22', '#7454a0', '#46865b']


def setup():
    available = {f.name for f in font_manager.fontManager.ttflist}
    font = next((f for f in ['Malgun Gothic', 'AppleGothic', 'NanumGothic', 'Noto Sans CJK KR'] if f in available), None)
    if not font:
        warnings.warn('Korean font unavailable: using English chart labels')
    plt.rcParams.update({'font.family': font or 'DejaVu Sans', 'font.size': 10,
                         'axes.titlesize': 13, 'axes.titleweight': 'bold',
                         'axes.labelcolor': NAVY, 'text.color': NAVY,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.edgecolor': '#c5ccd3', 'axes.unicode_minus': False,
                         'figure.facecolor': '#f7f8fa', 'axes.facecolor': '#ffffff',
                         'savefig.facecolor': '#f7f8fa', 'grid.alpha': .22})
    return bool(font)


def save(fig, path):
    fig.savefig(path, dpi=180, bbox_inches='tight', pad_inches=.24)
    plt.close(fig)


def date_axis(ax):
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax.grid(axis='y')


def marker(ax):
    ax.axvline(pd.Timestamp('2026-03-02'), color=RED, ls='--', lw=1, alpha=.7)


def oil_figure(long, short, path):
    if long.empty or short.empty:
        return False
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), layout='constrained', gridspec_kw={'width_ratios': [1.5, 1]})
    for ax, frame, title in zip(axes, [long, short], ['Long window · Feb–Mar 2026', 'Short window · Feb 24–Mar 15']):
        for ticker, label, color in [('BZ=F','Brent',BLUE),('CL=F','WTI',NAVY)]:
            ax.plot(frame.index, frame[ticker], label=label, color=color, lw=2)
        marker(ax)
        ax.set(title=title, ylabel='Futures Close (USD / barrel)', xlabel='2026 · market date')
        date_axis(ax)
        ax.legend(frameon=False)
    axes[1].xaxis.set_major_locator(mdates.DayLocator(interval=4))
    fig.suptitle('01  |  Brent & WTI futures around the event', fontsize=17, weight='bold')
    fig.supxlabel('Dashed line: Mar 02 · first US trading day after Feb 28 event. Panels use independent y-scales.', fontsize=9)
    save(fig, path)
    return True


def reaction_figure(reactions, path, korean):
    selected = reactions[reactions.include_main & reactions.return_pct.notna()]
    if selected.empty:
        return False
    fig, axes = plt.subplots(1, 2, figsize=(13, 8.7), sharex=True, layout='constrained')
    low = min(-3, selected.return_pct.min() - 2)
    high = max(6, selected.return_pct.max() * 1.16)
    span = high - low
    for ax, country, title in zip(axes, ['US','KR'], ['US · Feb 27 → Mar 02', 'Korea · Feb 27 → Mar 03']):
        group = selected[selected.country == country].sort_values('return_pct')
        labels = [r.company if korean and country == 'KR' else r.ticker for r in group.itertuples()]
        ax.barh(labels, group.return_pct, color=[BLUE if v >= 0 else RED for v in group.return_pct], height=.67)
        for y, value in enumerate(group.return_pct):
            ax.text(value + (span * .016 if value >= 0 else -span * .016), y, f'{value:+.1f}',
                    va='center', ha='left' if value >= 0 else 'right', fontsize=9)
        ax.axvline(0, color=NAVY, lw=.8)
        ax.set(title=f'{title} · n={len(group)}', xlim=(low, high), xlabel='Close-to-close return (%)')
        ax.grid(axis='x')
    fig.suptitle('02  |  First-session reactions differ across companies', fontsize=17, weight='bold')
    fig.supxlabel('Baseline: exact Feb 27 Close · US main sample excludes TPL post hoc; all 21 retained in tables.\nEach market uses its own first session; elapsed time differs. Same x-scale in both panels.', fontsize=9)
    save(fig, path)
    return True


def industry_figure(frame, us, baseline, path):
    pct = returns_from(frame, baseline)
    main = us[us.include_main]
    if pct.dropna(how='all').empty:
        return False
    fig, axes = plt.subplots(3, 2, figsize=(13, 10), sharex=True, sharey=True, layout='constrained')
    industries = list(main.sub_industry.unique())
    for ax, industry, color in zip(axes.flat, industries, PALETTE):
        group = main[main.sub_industry == industry]
        for i, row in enumerate(group.itertuples()):
            ax.plot(pct.index, pct[row.ticker], lw=1.7, label=row.ticker, alpha=.85, ls=['-','--',':','-.'][i % 4])
        ax.set_title(industry.replace('Oil & Gas ', ''), color=color)
        ax.axhline(0, color=GRAY, lw=.7)
        marker(ax)
        date_axis(ax)
        ax.legend(ncol=3, frameon=False, fontsize=8)
        ax.set_ylabel('Return (%)')
    axes.flat[-1].axis('off')
    axes.flat[-1].text(.02, .75, 'Same y-scale in every panel\nBaseline: Feb 27, 2026 Close\nMain sample: 20 US companies\nTPL kept in initial-sample tables\n\nDashed event marker: Mar 02\nNo market-return adjustment', transform=axes.flat[-1].transAxes, linespacing=1.7)
    fig.suptitle('03  |  Within-industry paths · event baseline', fontsize=17, weight='bold')
    save(fig, path)
    return True


def hd_figure(frame, revenue, baseline, path, korean):
    hd = revenue[revenue.ticker == '267250.KS']
    pct = returns_from(frame.reindex(columns=['267250.KS', '010950.KS']), baseline)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.3), layout='constrained')
    labels = hd.segment if korean else ['Shipbuilding / offshore','Refining','Construction machinery','Electrical / electronics','Marine services']
    axes[0].barh(list(labels)[::-1], hd.pct.to_numpy()[::-1], color=[GRAY,GRAY,GRAY,BLUE,NAVY])
    for y, val in enumerate(hd.pct.to_numpy()[::-1]):
        axes[0].text(val + .7, y, f'{val:g}%', va='center')
    axes[0].set(title='HD Hyundai · original revenue entries', xlabel='User-provided share (%)', xlim=(0,52))
    axes[0].grid(axis='x')
    if not pct.dropna(how='all').empty:
        for t, label, color in [('267250.KS','HD Hyundai',NAVY), ('010950.KS','S-Oil',BLUE)]:
            axes[1].plot(pct.index, pct[t], label=label, color=color, lw=2)
        axes[1].axvline(pd.Timestamp('2026-03-03'), ls='--', color=RED, lw=1)
        axes[1].axhline(0, color=GRAY, lw=.7)
        axes[1].legend(frameon=False)
        date_axis(axes[1])
        axes[1].set(title='Observed share-price paths', ylabel='Return from Feb 27 Close (%)')
    else:
        axes[1].text(.1, .5, 'Price panel unavailable: no exact baseline data', transform=axes[1].transAxes)
        axes[1].axis('off')
    fig.suptitle('04  |  From an oil-related label to actual business segments', fontsize=17, weight='bold')
    fig.supxlabel('Revenue source: user transcription (2025.12); total 99.6%, no renormalization.\nOther 0.38% from the described capture is not appended. These panels do not establish causation.', fontsize=9)
    save(fig, path)
    return True


def grid_figure(frame, companies, path, baseline=None, three_dates=None):
    if frame.dropna(how='all').empty:
        return False
    fig, axes = plt.subplots(7, 3, figsize=(14, 20), sharex=True, sharey=three_dates is None, layout='constrained')
    if three_dates is not None:
        values = frame.reindex(pd.to_datetime(three_dates))
    else:
        values = returns_from(frame, baseline)
    for ax, row in zip(axes.flat, companies.itertuples()):
        series = values[row.ticker]
        ax.plot(series.index, series, lw=1.6, marker='o' if three_dates else None, ms=3, color=BLUE)
        if three_dates is None:
            ax.axhline(0, color=GRAY, lw=.7)
            marker(ax)
        else:
            ax.set_xticks(series.index)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax.tick_params(axis='x', labelsize=8)
            plt.setp(ax.get_xticklabels(), rotation=35, ha='right')
            ax.margins(x=.1, y=.18)
            for x, y in series.items():
                if pd.notna(y):
                    ax.annotate(f'{y:.2f}', (x,y), xytext=(0,5), textcoords='offset points', ha='center', fontsize=7)
        ax.set_title(row.ticker + (' · retained, excluded from main' if row.ticker == 'TPL' else ''), fontsize=10)
        if three_dates is None:
            date_axis(ax)
        ax.grid(axis='y')
    title = 'Initial 21 US companies · three exact-date Close prices (USD)' if three_dates else f'Initial 21 US companies · return from {baseline} first observation (%)'
    fig.suptitle(title, fontsize=16, weight='bold')
    fig.supxlabel('Independent y-scales: absolute prices are not directly comparable.' if three_dates else 'Shared y-scale · actual calendar dates · TPL retained for sample audit\nDashed marker: Mar 02 · first US trading day after the Feb 28 event', fontsize=10)
    save(fig, path)
    return True
