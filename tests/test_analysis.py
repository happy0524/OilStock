"""Small correctness checks; these do not validate any economic hypothesis."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.analysis import (returns_from, reaction_table, validate_prices,
                          match_revenue, revenue_quality)


def test_return_formula_and_nan_preservation():
    frame = pd.DataFrame({'X':[100.,110.,np.nan]}, index=pd.to_datetime(['2026-02-27','2026-03-02','2026-03-03']))
    result = returns_from(frame, '2026-02-27')
    assert result.X.iloc[0] == 0
    assert result.X.iloc[1] == pytest.approx(10)
    assert pd.isna(result.X.iloc[2])


@pytest.mark.parametrize('baseline',['2026-02-28','2026-03-02'])
def test_missing_baseline_never_uses_nearest_day(baseline):
    frame = pd.DataFrame({'X':[100.,np.nan,120.]}, index=pd.to_datetime(['2026-02-27','2026-03-02','2026-03-03']))
    assert returns_from(frame, baseline).X.isna().all()


def test_market_holiday_is_not_filled_from_us_date():
    frame = pd.DataFrame({'US':[100.,110.,115.], 'KR':[100.,np.nan,90.]},
                         index=pd.to_datetime(['2026-02-27','2026-03-02','2026-03-03']))
    companies = pd.DataFrame({'ticker':['US','KR'], 'company':['US','KR'], 'country':['US','KR'], 'include_main':[True,True]})
    result = reaction_table(frame, companies, '2026-02-27', {'US':'2026-03-02','KR':'2026-03-03'}).set_index('ticker')
    assert result.loc['US','return_pct'] == pytest.approx(10)
    assert result.loc['KR','return_pct'] == pytest.approx(-10)
    missing = reaction_table(frame, companies, '2026-02-27', {'US':'2026-03-02','KR':'2026-03-02'}).set_index('ticker')
    assert missing.loc['KR','status'] == 'missing_exact_date'
    assert pd.isna(missing.loc['KR','return_pct'])


def test_first_observation_differs_from_event_baseline():
    frame = pd.DataFrame({'X':[80.,100.,110.]}, index=pd.to_datetime(['2026-02-02','2026-02-27','2026-03-02']))
    assert returns_from(frame, frame.index[0]).X.iloc[-1] == pytest.approx(37.5)
    assert returns_from(frame, '2026-02-27').X.iloc[-1] == pytest.approx(10)


def test_duplicate_days_raise():
    with pytest.raises(ValueError, match='Duplicate'):
        validate_prices(pd.DataFrame({'X':[1,2]},index=['2026-02-27','2026-02-27']))


@pytest.mark.parametrize('price',[0,-1])
def test_nonpositive_close_raises(price):
    with pytest.raises(ValueError, match='Nonpositive'):
        validate_prices(pd.DataFrame({'X':[price]}, index=['2026-02-27']))


def test_matching_rejects_unknown_or_duplicate_security():
    revenue = pd.DataFrame({'ticker':['X'],'segment':['oil'],'pct':[100]})
    with pytest.raises(ValueError, match='Unmatched'):
        match_revenue(revenue, pd.DataFrame({'ticker':['Y'],'country':['US']}))
    with pytest.raises(ValueError, match='Duplicate company'):
        match_revenue(revenue, pd.DataFrame({'ticker':['X','X'],'country':['US','US']}))
    with pytest.raises(ValueError, match='Duplicate revenue'):
        match_revenue(pd.concat([revenue,revenue]), pd.DataFrame({'ticker':['X'],'country':['US']}))


def test_quality_preserves_negative_incomplete_and_excess_totals():
    revenue = pd.DataFrame({'ticker':['A','B','B'], 'company':['A','B','B'],
                            'pct':[80.1,106.2,-.94], 'classification':['oil_gas_explicit']*3})
    original = revenue.copy(deep=True)
    quality = revenue_quality(revenue).set_index('ticker')
    assert quality.loc['A','total_pct'] == pytest.approx(80.1)
    assert quality.loc['B','total_pct'] == pytest.approx(105.26)
    assert quality.loc['B','negative_count'] == 1
    pd.testing.assert_frame_equal(revenue, original)


def test_missing_ticker_is_reported_instead_of_zero():
    companies = pd.DataFrame({'ticker':['MISSING'],'company':['M'],'country':['US'],'include_main':[True]})
    result = reaction_table(pd.DataFrame(), companies, '2026-02-27', {'US':'2026-03-02'})
    assert result.status.iloc[0] == 'missing_exact_date'
    assert pd.isna(result.return_pct.iloc[0])
