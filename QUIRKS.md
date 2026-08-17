# Bootcheck grading quirks

Known gaps/quirks in `bootcheck/grading.py` where a model's response can be
legitimate, correct Cisco IOS-XE syntax but still fail grading. Logged here
rather than silently patched, per CLAUDE.md's rule against modifying
`grading.py`/`harness.py` without being explicitly asked. Each entry should
say what triggers it, why it's a false negative, and which task(s) it's been
observed on.

## `interface vlan 10` vs `interface Vlan10`

`_check_isolation()` compares the submode interface name in the response
against `isolation.interface` via an exact, case-folded string match. Real
IOS-XE accepts `interface vlan 10` (lowercase, with a space before the VLAN
number) as valid input — `show running-config` normalizes it to `Vlan10`,
but the raw CLI command a model would type is accepted either way. The
grader only tolerates the no-space `Vlan10` form, so a fully correct answer
written as `interface vlan 10` fails isolation for no real reason.

Observed on: `cisco-iosxe-svi-vlan` — in a 12-model free-tier sweep
(2026-08-16), 6 of 9 non-errored responses were otherwise fully correct
(all required lines, description, and save present) and failed solely on
this isolation mismatch. Only 1/9 models happened to write the no-space
`vlan10` form and passed.

## Provider quirks

Gaps outside `grading.py` — in how the harness talks to a provider — that can
silently produce misleading results if not accounted for.

### OpenRouter model IDs need an explicit `:free` suffix for zero-cost calls

`--provider openrouter` model IDs are not guaranteed free just because the
same bare ID (e.g. `google/gemma-4-31b-it`) is free on Requesty, or because
it appears without a suffix elsewhere. On OpenRouter, passing the plain ID
without `:free` can silently resolve to a paid variant of the same model —
confirmed 2026-08-17: `google/gemma-4-31b-it` on `--provider openrouter`
returned `cost_usd: 4.066e-05` (not free), while the same model requested as
`google/gemma-4-31b-it:free` returned `cost_usd: 0.0`. `list_free_models()`
for the openrouter client already returns the correct `:free`-suffixed IDs —
this only bites if a model ID is typed in manually (e.g. copied from a
Requesty run) instead of sourced from that list.
