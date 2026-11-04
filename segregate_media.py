import os
import sys
import sqlite3
import json
import shutil
import argparse
import urllib.parse
from collections import defaultdict
from datetime import datetime

def find_image_files(images_dir):
    """Scan directory recursively for all image files."""
    valid_exts = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'}
    image_paths = {} # filename -> full_path
    
    print(f"Scanning for images in: {images_dir}")
    for root, _, files in os.walk(images_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in valid_exts:
                image_paths[f] = os.path.join(root, f)
                
    print(f"Found {len(image_paths)} unique image files.")
    return image_paths

def load_db_tasks(db_path):
    """Load tasks and fileupload records from SQLite database."""
    print(f"Loading database from: {db_path}")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Load fileupload records
    cur.execute("SELECT id, project_id, file FROM data_import_fileupload;")
    fileupload_map = {r[0]: (r[1], r[2]) for r in cur.fetchall()}

    # Load projects
    cur.execute("SELECT id, title FROM project;")
    project_titles = dict(cur.fetchall())

    # Load tasks
    cur.execute("SELECT id, project_id, data, file_upload_id, is_labeled FROM task;")
    tasks = cur.fetchall()

    tasks_info = []
    for tid, pid, data_str, fup_id, is_labeled in tasks:
        try:
            data = json.loads(data_str)
        except Exception:
            data = {}

        val = data.get('image') or data.get('$undefined$')
        if not val and data:
            val = list(data.values())[0] if isinstance(list(data.values())[0], str) else None

        if val and val.startswith('/data/'):
            relpath = val[len('/data/'):]
        elif fup_id and fup_id in fileupload_map:
            relpath = fileupload_map[fup_id][1]
        else:
            continue

        bname = os.path.basename(relpath)
        bname_unquoted = urllib.parse.unquote(bname)

        tasks_info.append({
            'task_id': tid,
            'project_id': pid,
            'project_title': project_titles.get(pid, 'Unknown'),
            'target_relpath': relpath, # e.g. upload/6/9c52f1e8-192.png
            'target_filename': bname,
            'target_filename_unquoted': bname_unquoted,
            'is_labeled': bool(is_labeled)
        })

    conn.close()
    print(f"Loaded {len(tasks_info)} tasks referencing media files.")
    return tasks_info, project_titles

def segregate_media(db_path, images_dir, output_dir, mode="copy"):
    """Match images and segregate them into media/upload/<project_id>/<filename>."""
    start_time = datetime.now()
    
    # 1. Discover all images
    avail_images = find_image_files(images_dir)
    
    # 2. Load DB tasks
    tasks_info, project_titles = load_db_tasks(db_path)

    # 3. Build lookup maps
    # target_filename -> list of task_info
    tasks_by_target = defaultdict(list)
    tasks_by_orig = defaultdict(list)
    missing_tasks = {}

    for t in tasks_info:
        tasks_by_target[t['target_filename']].append(t)
        if t['target_filename_unquoted'] != t['target_filename']:
            tasks_by_target[t['target_filename_unquoted']].append(t)

        parts = t['target_filename_unquoted'].split('-', 1)
        orig = parts[1] if (len(parts) == 2 and len(parts[0]) == 8) else t['target_filename_unquoted']
        tasks_by_orig[orig].append(t)
        missing_tasks[t['task_id']] = t

    # 4. Multi-tier Matching
    matches = [] # list of (src_path, dest_relpath, task_id, project_id, match_type)
    used_src_files = set()
    used_tasks = set()

    # Tier 1: Exact Filename Match
    for fname, src_path in avail_images.items():
        if fname in tasks_by_target:
            candidates = [c for c in tasks_by_target[fname] if c['task_id'] not in used_tasks]
            if candidates:
                cand = candidates[0]
                matches.append((src_path, cand['target_relpath'], cand['task_id'], cand['project_id'], 'exact'))
                used_src_files.add(fname)
                used_tasks.add(cand['task_id'])
                missing_tasks.pop(cand['task_id'], None)

    # Tier 2: Strip Export Hash Prefix
    for fname, src_path in avail_images.items():
        if fname in used_src_files:
            continue
        parts = fname.split('-', 1)
        if len(parts) == 2 and len(parts[0]) == 8:
            stripped = parts[1]
            if stripped in tasks_by_target:
                candidates = [c for c in tasks_by_target[stripped] if c['task_id'] not in used_tasks]
                if candidates:
                    cand = candidates[0]
                    matches.append((src_path, cand['target_relpath'], cand['task_id'], cand['project_id'], 'prefix_stripped'))
                    used_src_files.add(fname)
                    used_tasks.add(cand['task_id'])
                    missing_tasks.pop(cand['task_id'], None)

    # Tier 3: Match by Underlying Original Name
    for fname, src_path in avail_images.items():
        if fname in used_src_files:
            continue
        p = fname
        while len(p) > 9 and p[8] == '-':
            p = p[9:]
        if p in tasks_by_orig:
            candidates = [c for c in tasks_by_orig[p] if c['task_id'] not in used_tasks]
            if candidates:
                cand = candidates[0]
                matches.append((src_path, cand['target_relpath'], cand['task_id'], cand['project_id'], 'original_name'))
                used_src_files.add(fname)
                used_tasks.add(cand['task_id'])
                missing_tasks.pop(cand['task_id'], None)

    unmatched_files = [f for f in avail_images.keys() if f not in used_src_files]

    print(f"\n================ RESTORATION ANALYSIS ================")
    print(f"Total Available Images:     {len(avail_images):,}")
    print(f"Total Tasks in DB:          {len(tasks_info):,}")
    print(f"Total Matched & Restored:   {len(matches):,} ({len(matches)/len(avail_images)*100:.1f}% of images)")
    print(f"Unmatched Available Images: {len(unmatched_files):,}")
    print(f"Tasks Still Missing Images: {len(missing_tasks):,}")

    # Breakdown by match tier
    tier_counts = defaultdict(int)
    for m in matches:
        tier_counts[m[4]] += 1
    for tier, count in sorted(tier_counts.items()):
        print(f"  - Tier ({tier:<17}): {count:,} images")

    # Project distribution
    project_stats = defaultdict(lambda: {'count': 0, 'title': 'Unknown'})
    for m in matches:
        pid = m[3]
        project_stats[pid]['count'] += 1
        project_stats[pid]['title'] = project_titles.get(pid, 'Unknown')

    print(f"\nRestored Files Distribution Across Projects ({len(project_stats)} Projects):")
    for pid, st in sorted(project_stats.items(), key=lambda x: x[1]['count'], reverse=True):
        print(f"  Project {pid:<3} ({st['title'][:30]:<30}): {st['count']:,} images")

    # Check missing tasks
    missing_labeled = sum(1 for t in missing_tasks.values() if t['is_labeled'])
    missing_unlabeled = sum(1 for t in missing_tasks.values() if not t['is_labeled'])
    print(f"\nMissing Tasks Breakdown:")
    print(f"  - Labeled tasks missing:   {missing_labeled:,} ({(missing_labeled/len(tasks_info))*100:.2f}%)")
    print(f"  - Unlabeled tasks missing: {missing_unlabeled:,} ({(missing_unlabeled/len(tasks_info))*100:.2f}%)")

    # 5. File Operations
    if mode in ('copy', 'move', 'link'):
        print(f"\nExecuting file operations ({mode.upper()}) to: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
        copied = 0
        for src_path, dest_relpath, tid, pid, mtype in matches:
            dest_full = os.path.join(output_dir, dest_relpath)
            os.makedirs(os.path.dirname(dest_full), exist_ok=True)
            if os.path.exists(dest_full):
                copied += 1
                continue
            if mode == 'copy':
                shutil.copy2(src_path, dest_full)
            elif mode == 'move':
                shutil.move(src_path, dest_full)
            elif mode == 'link':
                try:
                    os.link(src_path, dest_full)
                except Exception:
                    shutil.copy2(src_path, dest_full)
            copied += 1
            if copied % 2000 == 0:
                print(f"  Processed {copied:,} / {len(matches):,} files...")
        print(f"File operations completed: {copied:,} files placed into {output_dir}.")
    else:
        print(f"\n[DRY-RUN] No files were copied or moved. Use --mode copy or --mode link to perform restoration.")

    # 6. Save JSON Report
    report = {
        'timestamp': datetime.now().isoformat(),
        'execution_seconds': (datetime.now() - start_time).total_seconds(),
        'total_images_scanned': len(avail_images),
        'total_tasks_in_db': len(tasks_info),
        'total_matched': len(matches),
        'tier_counts': dict(tier_counts),
        'projects_restored': {str(pid): st for pid, st in project_stats.items()},
        'unmatched_images_count': len(unmatched_files),
        'missing_tasks_count': len(missing_tasks),
        'missing_labeled_count': missing_labeled,
        'missing_unlabeled_count': missing_unlabeled,
    }

    report_path = os.path.join(output_dir if os.path.exists(output_dir) else ".", "restoration_summary.json")
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"Restoration report saved to: {report_path}")
    except Exception as e:
        print(f"Could not write report: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Segregate images into Label Studio media/upload structure")
    parser.add_argument("--db", default=r"C:\Users\MSheikMohammed\Downloads\label_studio.sqlite3", help="Path to label_studio.sqlite3")
    parser.add_argument("--images-dir", default=r"C:\Users\MSheikMohammed\Downloads\18k images", help="Path to images directory")
    parser.add_argument("--output-dir", default=r"D:\restored_media\media", help="Output media directory")
    parser.add_argument("--mode", choices=["dry-run", "copy", "move", "link"], default="dry-run", help="Execution mode (dry-run, copy, move, link)")
    args = parser.parse_args()

    segregate_media(args.db, args.images_dir, args.output_dir, args.mode)
