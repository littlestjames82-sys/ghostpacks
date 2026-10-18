# GhostPacks

**Shareable GhostSlice profile packs: stack knowledge as data.**

A good `.ghostslice.json` profile is earned knowledge: which folders
in a Next.js app are generated, which Django paths are migrations, how
a monorepo's packages should be sliced, which files are entry points.
GhostPacks gives that knowledge a format: a pack is a small,
human-readable folder of data (a manifest plus a GhostSlice profile
fragment) that can be shared, merged into a project, scored, and
removed cleanly.

By Ghost Developer Studio. Working name, companion #11 to GhostSlice.
Full plan: [PLAN.md](PLAN.md).

## Status

v0.1 in build (Oct 14, 2026). Core CLI, three starter packs, tests,
and examples are being built in parallel; this README describes the
v0.1 surface defined by PLAN.md. Nothing is published, pushed, or
priced, and no paid layer is decided.

## Hard rules (v0.1)

- **Data only.** A pack contains JSON and text a human can read top to
  bottom in minutes. Any executable or script file in a pack folder
  fails `ghostpacks lint`. The manager never installs, downloads, or
  executes plugin code; a pack may *reference* a plugin that the user
  already has, and that is all.
- **Local only, no network.** No registry, no marketplace, no update
  checker, no telemetry. Packs arrive by local folder or a git clone
  the user made themselves, and live in a local library folder
  (`~/.ghostpacks/` by default).
- **Context packs, never policy packs.** Every manifest carries
  `kind: "context"`. GhostPacks settings tune what an agent *reads*
  (GhostSlice's job); they grant no permissions and evaluate no
  policy. Agent Seatbelt and the GhostGuard family own that layer.
- **Previewed, explicit, reversible merges.** `merge` shows the full
  profile diff and requires an explicit yes. `remove` restores the
  pre-merge profile from the recorded backup, or explains exactly why
  it cannot (for example because the user edited the profile since)
  instead of guessing.
- **Honest scores.** A pack with no GhostBench result is labelled
  **unscored** everywhere it is shown. A pack that claims a Bench
  score must contain the Bench report file it references, or it
  fails lint.

## A pack

```
my-pack/
  pack.json       manifest
  profile.json    profile fragment in the exact .ghostslice.json schema
  bench-report.json   (only if the pack claims a Bench score)
  README.md       (optional, what the pack is for)
```

`pack.json`:

```json
{
  "id": "python-library",
  "version": "0.1.0",
  "kind": "context",
  "stack": ["python"],
  "ghostslice": ">=1.0,<2.0",
  "author": "Ghost Developer Studio",
  "date": "2026-10-14",
  "profile_file": "profile.json",
  "bench": {"score": 42.0, "report": "bench-report.json"}
}
```

`bench` is optional. Omit it and the pack is unscored. Include a
score and the referenced report file must exist in the pack.

`profile.json` is a fragment of a GhostSlice profile: top-level keys
from the `.ghostslice.json` schema only (`ignore`, `modes`, `model`,
`budget_tokens`, `entry_points`, `preset`, `auto_shrink`, `redact`,
`plugins`, `lint`, `duplicates`, `ci`). An unknown key fails the
merge with the key named, matching GhostSlice's loud-validation
discipline. Paths in a pack must be relative; absolute paths fail
lint.

## Usage

Run from a checkout, no install step (the interface the test suite
targets, see `tests/conftest.py`):

```bash
cd ghostpacks
PYTHONPATH=src python3 -m ghostpacks lint  <pack-folder>
PYTHONPATH=src python3 -m ghostpacks show  <pack-folder>
PYTHONPATH=src python3 -m ghostpacks list
PYTHONPATH=src python3 -m ghostpacks merge <pack-folder> <project>
PYTHONPATH=src python3 -m ghostpacks remove <project> <pack-id>
PYTHONPATH=src python3 -m ghostpacks doctor [target]
PYTHONPATH=src python3 -m ghostpacks init-pack <project> -o <out-folder>
```

- `lint <pack>` validates a pack folder: manifest, `kind`, profile
  fragment against the live GhostSlice schema, no absolute paths,
  no executable or script files, and the Bench report exists if a
  score is claimed.
- `show <pack>` prints the pack summary, including its score or the
  word **unscored**.
- `merge <pack> <project>` previews the profile diff,
  asks for an explicit yes (`--yes` skips the prompt, the diff is
  still printed), then writes the merged
  `.ghostslice.json` and records provenance (pack id, version,
  source, date, profile hash) in `.ghostslice-packs.json` next to
  it. Sharing the profile plus that lockfile reproduces the setup.
- `remove <project> <pack-id>` reverses a merge from the
  recorded backup, or reports why it cannot reverse cleanly.
- `init-pack <project> -o <out>` drafts a pack from a tuned project profile
  (manifest skeleton plus fragment, absolute paths stripped). A
  draft still needs `lint` and a Bench run before it can claim a
  score.

## Starter packs

Three packs ship in `packs/` (see PLAN.md), Bench Tier A scored on
stated reference projects or labelled unscored:

- `python-library`: Python library layout conventions.
- `nextjs-typescript`: Next.js / TypeScript app conventions.
- `monorepo`: multi-package layout built on GhostSlice workspace
  detection.

A pack whose Bench result is embarrassing ships with the number
shown, or does not ship. No silent cherry-picking.

## Examples

`examples/` contains a small unscored demo pack
(`examples/demo-python-pack/`) and a two-file fixture project
(`examples/fixture-project/`) you can merge it into and remove it
from by hand. See `examples/README.md`.

## Tests

```bash
PYTHONPATH=src python3 -m pytest tests -q
```

The suite covers the PLAN.md verification bar: a tampered pack
containing an executable file fails lint, an unknown profile key
fails merge with the key named, merge/remove restores the pre-merge
GhostSlice export totals exactly, unscored packs are labelled, and a
claimed score without its Bench report fails lint. The round-trip
test uses the real GhostSlice exporter from the sibling
`~/workspace/ghostslice` checkout (override with `GHOSTSLICE_SRC`).

## Out of scope (v0.1)

Hosted registry or marketplace, ratings, accounts, payments,
auto-updates, telemetry, pack signing, installing or executing
plugin code, and automatic (agent-initiated) merges. A human runs
merge.

## Honest notes

- Stack packs rot as frameworks release majors. Packs carry stack
  tags and dates, and `doctor` flags out-of-range use as a warning
  with the range printed, never a silent pass.
- Token and savings figures come from GhostSlice's estimator and a
  local, dated price table. They are estimates, labelled as such.
- A bad pack can silently worsen context for everyone who trusts
  it. Bench scoring, diff preview, and reversibility exist for that
  reason; read a pack before you merge it.

## License

MIT core, same pattern as GhostSlice, Agent Seatbelt, and Ghost
Hands. Pricing for any future maintained pack library is not
decided.
