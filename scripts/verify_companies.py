"""Verify current Korean ticker/name/market against official KIND listings."""
import argparse
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
import re
import json
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]


def kind_listing(market, refresh=False):
    kind = {'KOSPI': 'stockMkt', 'KOSDAQ': 'kosdaqMkt'}[market]
    url = f'https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&marketType={kind}'
    cache = ROOT / 'data/raw' / f'kind_{market}.html'
    meta_file = cache.with_suffix('.json')
    if cache.exists() and meta_file.exists() and not refresh:
        html = cache.read_text(encoding='utf-8')
        meta = json.loads(meta_file.read_text(encoding='utf-8'))
    else:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        html = response.content.decode('euc-kr')
        meta = {'url': url, 'fetched_at_utc': datetime.now(timezone.utc).isoformat()}
        cache.write_text(html, encoding='utf-8')
        meta_file.write_text(json.dumps(meta), encoding='utf-8')
    frame = pd.read_html(StringIO(html), converters={'종목코드': str})[0]
    frame['종목코드'] = frame['종목코드'].str.zfill(6)
    return frame, meta


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'data/reference/kr_companies.csv'
    companies = pd.read_csv(path, dtype={'code': str})
    records = []
    normalized = lambda s: re.sub(r'[^a-z0-9가-힣]', '', s.lower())
    for market in ['KOSPI', 'KOSDAQ']:
        try:
            listing, meta = kind_listing(market, args.refresh)
            for row in companies[companies.market == market].itertuples(index=False):
                matches = listing[listing['회사명'].map(normalized) == normalized(row.company)]
                if len(matches) == 0 and row.company == '세기상사':
                    # Historical provided name; current official listing keeps the same security code.
                    matches = listing[(listing['종목코드'] == row.code) & (listing['회사명'] == '우양피앤엘')]
                found_code = matches['종목코드'].iloc[0] if len(matches) == 1 else ''
                status = 'verified_KIND_current' if found_code == row.code else 'code_mismatch_or_missing'
                if status == 'verified_KIND_current' and row.company == '세기상사':
                    status = 'verified_code_market_current_name_differs'
                records.append(dict(ticker=row.ticker, expected_company=row.company,
                                    provider_company=matches['회사명'].iloc[0] if len(matches) == 1 else '',
                                    expected_code=row.code, provider_code=found_code,
                                    expected_market=market, provider_market=market if len(matches) == 1 else '',
                                    status=status, **meta, error=''))
        except Exception as exc:
            for row in companies[companies.market == market].itertuples(index=False):
                records.append(dict(ticker=row.ticker, expected_company=row.company, provider_company='',
                                    expected_code=row.code, provider_code='', expected_market=market,
                                    provider_market='', status='failed', url='', fetched_at_utc='', error=str(exc)))
    audit = pd.DataFrame(records)
    (ROOT / 'data/processed').mkdir(exist_ok=True)
    audit.to_csv(ROOT / 'data/processed/company_verification.csv', index=False, encoding='utf-8-sig')
    companies['verification_status'] = companies.ticker.map(audit.set_index('ticker').status)
    companies['verification_url'] = companies.ticker.map(audit.set_index('ticker').url)
    companies.to_csv(path, index=False, encoding='utf-8-sig')
    print(audit[['ticker', 'provider_company', 'provider_code', 'provider_market', 'status']].to_string(index=False))


if __name__ == '__main__':
    main()
