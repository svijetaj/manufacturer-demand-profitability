# Working agreement

Weekend project, twelve people, one deadline. These rules exist so we don't spend
the time merging instead of building.

## Claim before you build

Open an issue from the workstream template, or claim in the department thread.
Two people on the same workstream is fine; two people on it silently is not.

## Branches

`ws-<letter>-<short-name>` — e.g. `ws-a-semantic-layer`, `ws-g-eval`.
PR into `main`. One reviewer. No direct pushes to `main`.

## Data

Do not commit CSVs. Run `make data` — the generator is the source of truth, so
everyone regenerates identical files from the same seed.

**Never commit real company data.** Not anonymised, not "close to real", not in a
notebook output cell. CI blocks committed CSVs, but it cannot see inside a saved
notebook — that one is on you. If you are unsure, ask before you push.

## The answer key

`eval/answer_key.yaml` lists the findings planted in the generated data. It is
how we measure the agent. **Do not paste it into an agent prompt** — that turns
the eval into a memory test.

## Recaps

When a workstream lands something, post a short recap in the department thread
and log any real decision in `docs/DECISIONS.md`. Decisions made only in chat
get lost, and we will re-argue them at 11pm.
