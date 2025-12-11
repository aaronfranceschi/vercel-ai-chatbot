"""CLI wrapper for downloading public-domain images from MET OpenAccess CSV.

Example:
    python main.py --csv https://github.com/metmuseum/openaccess/raw/master/MetObjects.csv --out images --workers 10 --max 50
"""
import argparse
import sys
from pathlib import Path

from downloader import download_public_domain_images
from rate_limiter import HostRateLimiter
from reporter import write_report


def main():
    p = argparse.ArgumentParser(description='Download public-domain images from MET OpenAccess CSV')
    p.add_argument('--csv', required=True, help='Path or URL to the CSV file')
    p.add_argument('--out', default='images', help='Output directory')
    p.add_argument('--workers', type=int, default=8, help='Concurrent download workers')
    p.add_argument('--max', type=int, default=0, help='Maximum number of public-domain rows to process (0 = all)')
    p.add_argument('--link-key', default='Link Resource', help='CSV column with object page URL')
    p.add_argument('--pd-key', default='Public Domain', help='CSV column indicating public domain')
    args = p.parse_args()

    max_items = args.max if args.max and args.max > 0 else None
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rate_limiter = HostRateLimiter(min_delay=args.delay) if args.delay and args.delay > 0 else None

    print(f"Reading CSV: {args.csv}")
    results = download_public_domain_images(
        args.csv,
        output_dir=str(out),
        workers=args.workers,
        max_items=max_items,
        link_key=args.link_key,
        public_domain_key=args.pd_key,
        rate_limiter=rate_limiter,
    )

    ok = sum(1 for r in results if r[2] == 'ok')
    total = len(results)
    print(f"Completed: {ok}/{total} images downloaded")
    for row, dest, status in results:
        if status != 'ok':
            print(f"Failed: {status} - link={row.get(args.link_key)}")

    if args.report:
        write_report(args.report, results)
        print(f"Wrote report to {args.report}")


if __name__ == '__main__':
    main()
