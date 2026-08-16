# Repo instructions

- Never add a `Co-Authored-By: Claude` (or any AI co-author) trailer to commit messages in this repo.
- Every command run in this repo must be accompanied by a description and a justification for why
  it's being run — not just a label for what it does.

## Branching strategy

`main` <- `dev` <- semantic branches.

- `main`: stable/release branch.
- `dev`: integration branch. All work lands here before it reaches `main`.
- Semantic branches: cut from `dev` for each unit of work, named with a Conventional Commits-style
  prefix, e.g. `feat/bootcheck-bgp-task`, `fix/free-model-fallback`, `chore/pyproject-migration`,
  `docs/results-schema`. Merge back into `dev`; `dev` is merged into `main` periodically once stable.

## Bootcheck task authoring

- Before writing a Cisco IOS-XE bootcheck task's `expected_config` / `pass_criteria`, look up a real
  Cisco IOS-XE configuration guide example for the feature under test (official Cisco documentation)
  to ground the answer key in verified syntax rather than assumption.
- Every task must set a `category` field (alongside `vendor`/`os_train`/`tier`) so results can be
  rolled up by function independent of vendor — this is what makes the benchmark's dashboard
  cross-vendor. Current values: `interface-config`, `static-routing`. Add a new category only when a
  task genuinely doesn't fit an existing one; don't create near-duplicate categories.
- All example IP addressing in task configs must use RFC 5737 documentation space
  (`192.0.2.0/24` aka NET-1, `198.51.100.0/24`, aka NET-2, `203.0.113.0/24`, aka NET-3) rather than
  RFC 1918 private ranges. Only use NET-2 and NET-3 in examples requiring multiple networks.
- Use Cisco's proper/official terminology in task prompts and titles (e.g. "interface", not the
  colloquial "port") rather than maintaining a separate glossary.

## Autonomous / overnight (/loop) work

When running unattended via /loop or scheduled wakeups in this repo:
- Never merge a feature branch into `dev` without the user present to review it. Commit work to
  `feat/*` branches and stop there; leave merges for the user.
- Never push to any remote.
- Stay strictly within the scope given for that loop session — do not invent additional tasks,
  vendors, or scope (e.g. VM/containerlab work) beyond what was explicitly requested.
- Do not modify existing harness/grading code (`bootcheck/harness.py`, `bootcheck/grading.py`) or
  existing task fixtures unless explicitly asked to for that session. If a genuine bug is found,
  note it for the user rather than fixing it unasked.
