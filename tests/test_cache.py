from pathlib import Path
import sys
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.collect import collect


def test_cache_reuse_and_checksum_validation(tmp_path, monkeypatch):
    (tmp_path / 'data/raw').mkdir(parents=True)
    calls = []
    def download(*args, **kwargs):
        calls.append(kwargs)
        return pd.DataFrame({('Close','X'):[100.,110.]}, index=pd.to_datetime(['2026-02-27','2026-03-02']))
    monkeypatch.setattr('src.collect.yf.download',download)
    window = {'requested_start':'2026-02-27','end_exclusive':'2026-03-03'}
    frame, first = collect(tmp_path,'test',['X'],window,False)
    cached, second = collect(tmp_path,'test',['X'],window,False,offline=True)
    assert len(calls) == 1
    assert calls[0]['auto_adjust'] is False
    pd.testing.assert_frame_equal(frame,cached)
    assert second[0]['cache_used'] is True
    assert second[0]['actual_last_date'] == '2026-03-02'
    cache = next((tmp_path / 'data/raw').glob('*.csv'))
    cache.write_text('corrupted', encoding='utf-8')
    with pytest.raises(ValueError,match='checksum'):
        collect(tmp_path,'test',['X'],window,False,offline=True)


def test_missing_offline_cache_is_explicit(tmp_path):
    (tmp_path / 'data/raw').mkdir(parents=True)
    frame, audit = collect(tmp_path,'absent',['X'],{'requested_start':'2026-02-27','end_exclusive':'2026-03-03'},False,offline=True)
    assert frame.empty
    assert audit[0]['status'] == 'empty_or_missing_ticker'
    assert 'Offline mode' in audit[0]['error']
