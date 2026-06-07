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

This runs local rule review, `ADD RECORD` style fresh group creation, attachment
upload, attachment verify, and full remote verify.

5. Archive and stop completed trial containers:

```bash
bash batch_runner.sh archive-completed
```

## Completion Gates

- `trial_log.csv` has exactly 35 unique 24-hex sessions.
- Each prompt has the expected 5 models.
- `bash batch_runner.sh review` passes before table submission.
- Fresh Bitable group is exactly `1 + 7 + 35`.
- Root row has `Dockerfile`, `repo.zip`, and build screenshot.
- Every rollout row has `git_diff`.
- Remote verification passes after filling.
- Completed `*-trial` task containers are stopped before the next task starts.

## Safety Rules

- Never fill a new task into an existing task group.
- Use `submit_new_task_group.py` and `submit_new_task_attachments.py` for writes.
- Keep browser clicks for inspection only.
- Do not remove shared browser or agent containers during trial archive.
