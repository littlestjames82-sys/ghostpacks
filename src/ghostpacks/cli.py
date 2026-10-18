"""GhostPacks command line.

    ghostpacks lint <pack>
    ghostpacks list [--library DIR]
    ghostpacks show <pack-or-id> [--library DIR]
    ghostpacks merge <pack> <project> [--yes] [--force] [--library DIR]
    ghostpacks remove <project> <pack-id> [--yes] [--force]
    ghostpacks doctor [target] [--library DIR]
    ghostpacks init-pack <project> -o <out> [--id ID] [--stack a,b]

Exit codes: 0 ok, 1 lint failure / merge conflict / declined state
that the caller should treat as not-done, 2 usage or config errors.
Local folders only: this CLI contains no network or download code.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .authoring import create_pack_from_project
from .doctor import doctor_pack, doctor_project, format_report
from .manager import merge_pack, remove_pack
from .pack import (GhostPacksError, default_library_dirs, find_packs,
                   lint_pack, load_pack, resolve_pack)


def _is_pack_dir(path) -> bool:
    return (Path(path) / "pack.json").is_file()


def cmd_lint(args) -> int:
    errors, warnings = lint_pack(args.pack)
    for w in warnings:
        print(f"warning: {w}")
    if errors:
        for e in errors:
            print(f"error: {e}")
        print(f"lint: FAIL ({len(errors)} error(s))")
        return 1
    pack = load_pack(args.pack)
    print(f"lint: OK - {pack.summary_line()}")
    return 0


def cmd_list(args) -> int:
    dirs = default_library_dirs(args.library)
    print("library: " + ", ".join(str(d) for d in dirs))
    folders = find_packs(dirs)
    if not folders:
        print("(no packs found in the local library)")
        return 0
    if args.json:
        rows = []
        for folder in folders:
            try:
                pack = load_pack(folder)
                rows.append({"id": pack.id, "version": pack.version,
                             "kind": "context", "stack_tags": pack.stack_tags,
                             "score_status": pack.score_status,
                             "path": str(folder)})
            except GhostPacksError as exc:
                rows.append({"path": str(folder), "error": str(exc)})
        print(json.dumps(rows, indent=2))
        return 0
    for folder in folders:
        try:
            pack = load_pack(folder)
            print(f"{pack.summary_line()}  {folder}")
        except GhostPacksError as exc:
            print(f"INVALID PACK at {folder}: {exc}")
    return 0


def cmd_show(args) -> int:
    pack_dir = resolve_pack(args.pack, default_library_dirs(args.library))
    pack = load_pack(pack_dir)
    if args.json:
        print(json.dumps({"manifest": pack.manifest, "profile": pack.profile,
                          "score_status": pack.score_status,
                          "path": str(pack_dir)}, indent=2))
        return 0
    print(pack.summary_line())
    print(f"path: {pack_dir}")
    manifest = pack.manifest
    if manifest.get("description"):
        print(f"description: {manifest['description']}")
    if manifest.get("author"):
        print(f"author: {manifest['author']}")
    if manifest.get("date"):
        print(f"date: {manifest['date']}")
    print(f"ghostslice range: {pack.slice_range or '(not stated)'}")
    print(f"score status: {pack.score_status}"
          + (f" (score {pack.claimed_score}, report {pack.bench_report})"
             if pack.score_status == "scored" else
             " - no Bench report backs this pack; savings are unmeasured"))
    if manifest.get("reference_projects"):
        print(f"reference projects: {manifest['reference_projects']}")
    print("profile fragment:")
    print(json.dumps(pack.profile, indent=2, sort_keys=True))
    return 0


def cmd_merge(args) -> int:
    dirs = default_library_dirs(args.library)
    if args.pack and args.project:
        first, second = args.pack, args.project
    elif args.pack:
        raise GhostPacksError("merge needs a pack and a project folder")
    else:
        raise GhostPacksError("merge needs a pack and a project folder")
    # Accept either order: whichever side is a pack folder is the pack.
    if _is_pack_dir(first) and not _is_pack_dir(second):
        pack_arg, project = first, second
    elif _is_pack_dir(second) and not _is_pack_dir(first):
        pack_arg, project = second, first
    else:
        pack_arg, project = first, second
    pack_dir = resolve_pack(pack_arg, dirs)
    result = merge_pack(project, pack_dir, assume_yes=args.yes,
                        force=args.force)
    return 0 if result["status"] in ("merged", "unchanged") else 1


def cmd_remove(args) -> int:
    project, pack_id = args.project, args.pack
    # Tolerate swapped order when the first arg is a bare pack id that
    # does not exist as a folder while the second does.
    if not Path(project).is_dir() and Path(pack_id).is_dir():
        project, pack_id = pack_id, project
    result = remove_pack(project, pack_id, assume_yes=args.yes,
                         force=args.force)
    return 0 if result["status"] == "removed" else 1


def cmd_doctor(args) -> int:
    target = Path(args.target) if args.target else Path.cwd()
    if _is_pack_dir(target):
        report = doctor_pack(target)
    elif (target / "pack.json").is_file():
        report = doctor_pack(target)
    else:
        report = doctor_project(target, default_library_dirs(args.library))
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_report(report))
    return 0 if report["ok"] else 1


def cmd_init_pack(args) -> int:
    stack = [s.strip() for s in args.stack.split(",")] if args.stack else []
    result = create_pack_from_project(
        args.project, args.out, pack_id=args.id, name=args.name,
        author=args.author, stack_tags=[s for s in stack if s],
        force=args.force)
    print(f"draft pack {result['pack_id']} written to {result['out_dir']} "
          f"(unscored; files: {', '.join(result['files'])})")
    for item in result["stripped"]:
        print(f"stripped absolute path: {item}")
    print("next: read the draft, run `ghostpacks lint`, and bench it "
          "before claiming a score")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ghostpacks",
        description="Shareable, data-only GhostSlice context packs: "
                    "lint, list, show, merge, remove, doctor, init-pack. "
                    "Local folders only; no network, no code installation.")
    p.add_argument("--version", action="version",
                   version=f"ghostpacks {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("lint", help="validate a pack folder")
    sp.add_argument("pack")
    sp.set_defaults(fn=cmd_lint)

    sp = sub.add_parser("list", help="list packs in the local library")
    sp.add_argument("--library")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_list)

    sp = sub.add_parser("show", help="show one pack (id or folder)")
    sp.add_argument("pack")
    sp.add_argument("--library")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_show)

    sp = sub.add_parser("merge", help="merge a pack into a project profile "
                                      "(preview + explicit yes; either arg order)")
    sp.add_argument("pack")
    sp.add_argument("project")
    sp.add_argument("--library")
    sp.add_argument("--yes", action="store_true",
                    help="skip the confirmation prompt (diff still printed)")
    sp.add_argument("--force", action="store_true",
                    help="let the pack win on conflicting keys")
    sp.set_defaults(fn=cmd_merge)

    sp = sub.add_parser("remove", help="reverse a recorded pack merge in a project")
    sp.add_argument("project")
    sp.add_argument("pack", help="pack id as recorded in the lockfile")
    sp.add_argument("--yes", action="store_true")
    sp.add_argument("--force", action="store_true",
                    help="restore the backup even if the profile was edited "
                         "or later packs were merged")
    sp.set_defaults(fn=cmd_remove)

    sp = sub.add_parser("doctor", help="check a pack folder or a project")
    sp.add_argument("target", nargs="?", default=None)
    sp.add_argument("--library")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_doctor)

    sp = sub.add_parser("init-pack", help="draft a pack from a project's tuned profile")
    sp.add_argument("project")
    sp.add_argument("-o", "--out", required=True)
    sp.add_argument("--id", dest="id")
    sp.add_argument("--name")
    sp.add_argument("--author")
    sp.add_argument("--stack", help="comma-separated stack tags")
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(fn=cmd_init_pack)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except GhostPacksError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
