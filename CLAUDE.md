# Repo instructions

- Never add a `Co-Authored-By: Claude` (or any AI co-author) trailer to commit messages in this repo.

## Branching strategy

`main` <- `dev` <- semantic branches.

- `main`: stable/release branch.
- `dev`: integration branch. All work lands here before it reaches `main`.
- Semantic branches: cut from `dev` for each unit of work, named with a Conventional Commits-style
  prefix, e.g. `feat/bootcheck-bgp-task`, `fix/free-model-fallback`, `chore/pyproject-migration`,
  `docs/results-schema`. Merge back into `dev`; `dev` is merged into `main` periodically once stable.
