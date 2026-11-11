"""Yahoo Close collection with versioned cache and per-ticker provenance."""
import hashlib
import importlib.metadata
import json
import platform
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf
from src.analysis import validate_prices


def versions():
    return {'python': platform.python_version(), **{
        p: importlib.metadata.version(p) for p in ['pandas', 'numpy', 'matplotlib', 'yfinance', 'requests']}}


def collect(root, name, tickers, window, auto_adjust, refresh=False, offline=False):
    spec = dict(name=name, tickers=list(tickers), **window, auto_adjust=auto_adjust,
                source='Yahoo Finance via yfinance', field='Close', interval='1d')
    key = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:16]
    path = root / 'data/raw' / f'{name}_{key}.csv'
    meta_path = path.with_suffix('.json')
    cache_used = False
    if path.exists() and meta_path.exists() and not refresh:
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        if hashlib.sha256(path.read_bytes()).hexdigest() != meta['sha256']:
            raise ValueError(f'Cache checksum mismatch: {path.name}')
        frame = pd.read_csv(path, index_col=0, parse_dates=True)
        cache_used = True
    else:
        error = ''
        frame = pd.DataFrame(columns=tickers, index=pd.DatetimeIndex([], name='Date'), dtype=float)
        try:
            if offline:
                raise RuntimeError('Offline mode: required raw cache unavailable')
            raw = yf.download(list(tickers), start=window['requested_start'], end=window['end_exclusive'],
                              auto_adjust=auto_adjust, progress=False, threads=4, timeout=25)
            if raw.empty:
                raise ValueError('Yahoo returned empty dataset')
            close = raw['Close']
            if isinstance(close, pd.Series):
                close = close.to_frame(tickers[0])
            frame = validate_prices(close).reindex(columns=tickers)
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
        # Bad provider rows are retained in the raw cache when possible; validation errors are explicit.
        frame.index.name = 'Date'
        frame.to_csv(path, encoding='utf-8')
        meta = dict(spec, fetched_at_utc=datetime.now(timezone.utc).isoformat(), versions=versions(),
                    error=error, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8')
    frame = validate_prices(frame).reindex(columns=tickers)
    start, end = pd.Timestamp(window['requested_start']), pd.Timestamp(window['end_exclusive'])
    if ((frame.index < start) | (frame.index >= end)).any():
        raise ValueError('Provider returned dates outside requested half-open interval')
    records = []
    for ticker in tickers:
        valid = frame[ticker].dropna()
        records.append(dict(window=name, ticker=ticker, **window,
                            actual_first_date=str(valid.index.min().date()) if len(valid) else '',
                            actual_last_date=str(valid.index.max().date()) if len(valid) else '',
                            observations=len(valid), missing_on_union_dates=int(frame[ticker].isna().sum()),
                            status='ok' if len(valid) else 'empty_or_missing_ticker', error=meta.get('error', ''),
                            auto_adjust=auto_adjust, cache_used=cache_used,
                            fetched_at_utc=meta['fetched_at_utc'], raw_file=path.name, sha256=meta['sha256']))
    return frame, records
