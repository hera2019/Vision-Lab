"""Record host Git facts after image builds, before any experiment runs."""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def capture(root, disposable=False):
    base = root/'results/phase-6'
    read = lambda name: (base/name).read_text().strip()
    commit, tree = read('source-commit.txt'), read('source-tree.txt')
    upstream, origin = read('source-upstream.txt'), read('source-origin.txt')
    clean = not read('source-status-before.txt')
    standalone = (root/'.git').is_dir()
    no_alternates = not (root/'.git/objects/info/alternates').exists()
    valid_git_ids = bool(re.fullmatch('[0-9a-f]{40,64}', commit) and re.fullmatch('[0-9a-f]{40,64}', tree))
    context = {'run_id': read('run-id.txt'), 'captured_at_utc': datetime.now(timezone.utc).isoformat(),
        'source_commit': commit or None, 'source_tree': tree or None,
        'origin': origin or None, 'upstream_commit': upstream or None,
        'tracked_source_clean_at_entry': clean, 'standalone_git_directory': standalone,
        'no_git_object_alternates': no_alternates,
        'head_matches_tracking_revision': valid_git_ids and commit == upstream,
        'disposable_clone_declared': disposable,
        'context_kind': 'git-checkout' if standalone or (root/'.git').is_file() else 'source-snapshot',
        'fresh_clone_context_passed': bool(valid_git_ids and clean and standalone and no_alternates
            and origin and commit == upstream and disposable),
        'provenance_scope': 'Clean standalone Git checkout matching its recorded upstream revision, with owner disposable-clone declaration; not an independent reviewer verdict.'}
    (base/'source-context.json').write_text(json.dumps(context, indent=2)+'\n')
    return context


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--disposable', action='store_true')
    args = parser.parse_args()
    result = capture(Path('/work'), args.disposable)
    print(json.dumps({key: result[key] for key in ('run_id','context_kind','fresh_clone_context_passed')}))
