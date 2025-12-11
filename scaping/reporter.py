"""Reporting helpers to write CSV reports of download results."""
import csv


def write_report(path, results, fieldnames=None):
    fieldnames = fieldnames or ['ObjectID', 'Link', 'Status', 'SavedPath']
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for row, dest, status in results:
            out = {
                'ObjectID': row.get('Object ID') or row.get('ObjectID') or '',
                'Link': row.get('Link Resource') or row.get('Link') or row.get('link') or '',
                'Status': status,
                'SavedPath': dest or ''
            }
            w.writerow(out)
