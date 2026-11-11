"""Optional current candidate snapshots. Never modifies the historical fixed samples."""
import argparse
from datetime import datetime, timezone
from io import StringIO
import json
from pathlib import Path
import sys
import pandas as pd
import requests
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.collect import versions
from verify_companies import kind_listing


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--market-caps', action='store_true', help='Fetch current US market caps; not event-time caps')
    args = parser.parse_args()
    target = ROOT / 'data/raw/current_candidates.json'
    if target.exists() and not args.refresh:
        print('Using current-candidate snapshot cache. --refresh requests a new snapshot.')
        return 0
    result = dict(fetched_at_utc=datetime.now(timezone.utc).isoformat(), versions=versions(),
                  scope='current_execution_snapshot_not_event_constituents', errors=[], current_us=[], current_kr=[])
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        response = requests.get(url, headers={'User-Agent':'Mozilla/5.0'},timeout=30)
        response.raise_for_status()
        listing = pd.read_html(StringIO(response.text))[0]
        energy = listing[listing['GICS Sector'] == 'Energy'][['Symbol','Security','GICS Sector','GICS Sub-Industry']].copy()
        for row in energy.to_dict('records'):
            row.update(source=url, market_cap=None, market_cap_status='not_requested')
            if args.market_caps:
                try:
                    row['market_cap'] = yf.Ticker(row['Symbol'].replace('.','-')).info.get('marketCap')
                    row['market_cap_status'] = 'ok' if row['market_cap'] is not None else 'missing'
                except Exception as exc:
                    row['market_cap_status'] = f'failed: {exc}'
            result['current_us'].append(row)
    except Exception as exc:
        result['errors'].append(f'US: {type(exc).__name__}: {exc}')
    try:
        listing, meta = kind_listing('KOSPI', args.refresh)
        keywords = ['석유','에너지','가스','오일','정유','S-Oil','SK이노베이션','한국가스공사','GS','대성산업','흥구석유','중앙에너비스']
        candidates = listing[listing['회사명'].str.contains('|'.join(keywords),case=False,na=False)].copy()
        result['current_kr'] = candidates[['회사명','종목코드']].rename(columns={'회사명':'company','종목코드':'code'}).assign(
            market='KOSPI', source=meta['url'], market_cap_status='not_available_in_KIND_listing').to_dict('records')
    except Exception as exc:
        result['errors'].append(f'KR: {type(exc).__name__}: {exc}')
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"Current US candidates: {len(result['current_us'])}; KOSPI keyword matches: {len(result['current_kr'])}; errors: {result['errors']}")
    return 2 if result['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
