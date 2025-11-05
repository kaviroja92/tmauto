# main.py
import argparse
import asyncio
import logging

import config
from scanner import scan_initial_or_incremental
from arranger import build_groups
from poster import copy_group_to_arranged

logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, 'INFO'))

async def main():
    p = argparse.ArgumentParser()
    p.add_argument('--full', action='store_true', help='run full initial scan')
    p.add_argument('--scan', action='store_true', help='run incremental scan')
    p.add_argument('--make-groups', action='store_true', help='build groups and print counts')
    p.add_argument('--post-tag', type=str, help='post a single group tag from DB to arranged channel')
    p.add_argument('--dry-run', action='store_true', help='dry run poster')
    args = p.parse_args()

    if args.full:
        await scan_initial_or_incremental(full_scan=True)
    if args.scan:
        await scan_initial_or_incremental(full_scan=False)
    if args.make_groups:
        groups = await build_groups(config.DB_PATH)
        print('Total groups:', len(groups))
        for k,v in groups.items():
            print(k, len(v))
    if args.post_tag:
        groups = await build_groups(config.DB_PATH)
        items = groups.get(args.post_tag)
        if not items:
            print('Tag not found')
            return
        await copy_group_to_arranged(items, dry_run=args.dry_run)

if __name__ == '__main__':
    asyncio.run(main())