# Trae Trial Runbook

This workspace should keep one active task at a time in the root directory.
Completed task artifacts belong under `archive/<label>/`.

## Standard Flow

1. Prepare a clean `repo/`, root `Dockerfile`, `repo.zip`, and build screenshot.
2. Run preflight:

```bash
bash batch_runner.sh preflight
```

3. Run all missing prompt/model rollouts:

```bash
bash batch_runner.sh fullauto
```

4. Submit to a new Bitable task group, not an old group:

```bash
bash batch_runner.sh submit-fresh
```

This runs score_reason normalization, local rule review, fresh group creation,
attachment upload, docker build metadata, remote verify, and server-side
`score_reason` / `score_check` repair.

See `docs/bitable-submission-checklist.md` for the full anti-mistake checklist.

5. Archive and stop completed trial containers:

```bash
bash batch_runner.sh archive-completed
```

## Completion Gates

- `trial_log.csv` has exactly 35 unique 24-hex sessions.
- Each prompt has the expected 5 models.
- `bash batch_runner.sh review` passes before table submission.
- `score_reason` values are structured (not auto templates); see `bitable_score_reason.py`.
- Fresh Bitable group is exactly `1 + 7 + 35`.
- Root row has `Dockerfile`, `repo.zip`, and build screenshot.
- Every rollout row has `git_diff`.
- Remote verification passes after filling.
- Completed `*-trial` task containers are stopped before the next task starts.

## Current Feishu Standard

The latest downloaded standard is stored at
`docs/feishu-standard-current.md`.

Model rules currently remain strict:

- The required seed model is exactly `Doubao-Seed-2.0-Code`.
- `Doubao-Seed-1.8` and `Doubao-Seed-Code` are not approved substitutes.
- If a model is unavailable, times out, or the session is interrupted by a
  resource or engineering issue, retry and submit only a successful rollout.
- Do not score or archive `4023` / Auto-fallback / wrong-model sessions.
- Do not privately change models; model substitutions require explicit project
  owner approval.

## Safety Rules

- Never fill a new task into an existing task group.
- Use `submit_new_task_group.py` and `submit_new_task_attachments.py` for writes.
- Keep browser clicks for inspection only.
- Do not remove shared browser or agent containers during trial archive.
