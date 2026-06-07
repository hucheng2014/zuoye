# Alibaba LabelX Audio Caption Current-Page Workflow

This directory keeps the effective workflow used on 2026-06-06. It supports the current LabelX page whether it renders 1 task, 10 tasks, or another number of tasks.

## Core Flow

1. Generate captions offline:

```bash
/home/jianglei/zuoye/putonghuaasr/.venv/bin/python -u solve_current_page.py
```

This only extracts the tasks currently rendered on the page, downloads videos, generates captions, runs independent review, and writes `scratch/batch_current_results.json`. It does not fill or submit.

2. Run targeted review when a result has warnings or manual doubt:

```bash
/home/jianglei/zuoye/putonghuaasr/.venv/bin/python -u review_targets.py
```

The target script only reads local result/video files and writes `scratch/target_reviews.json`. By default it reviews all generated items. To review specific items:

```bash
/home/jianglei/zuoye/putonghuaasr/.venv/bin/python -u review_targets.py --items 1
/home/jianglei/zuoye/putonghuaasr/.venv/bin/python -u review_targets.py --items 2,4,7-8
```

3. Fill and verify persistence without submitting:

```bash
/home/jianglei/zuoye/putonghuaasr/.venv/bin/python -u solve_current_page.py --fill --use-results
```

The script verifies the current page still matches the generated results by index, original caption, and video duration before filling. It then fills every rendered task on the current page, checks page values, waits for save, reloads, and verifies persistence.

4. Submit only after fill/reload verification:

```bash
/home/jianglei/zuoye/putonghuaasr/.venv/bin/python -u solve_current_page.py --submit --use-results
```

The submit path repeats fill and reload verification, then performs a final page-level preflight check before clicking `提交任务`.

## Keep Files

- `solve_current_page.py`: official entrypoint for all tasks rendered on the current page.
- `solve_current_page_batch.py`: implementation module retained for compatibility. Despite the historical filename, it is not limited to 10 tasks.
- `solve_single_task.py`: formatter used by the batch workflow.
- `preflight_checks.py`: hard pre-submit checks for format, timestamps, language-dependent structure, and sound-effect rules.
- `review_targets.py`: independent targeted review for suspicious items.
- `new_rules_text_full.txt`: latest Feishu rule extraction used for the current workflow.
- `scratch/batch_current_results.json`: final generated result set for the last successful current page.
- `scratch/batch_current_submit_result.json`: submit confirmation for the last successful current page.
- `scratch/batch_item_XX_caption_final.txt`: final per-item captions used for the last successful current page.

## Submission Discipline

- Do not submit from `agent-browser`; use the production script.
- Do not trust a hard check alone. Verify actual filled page values and reload persistence before submit.
- Do not use old single-task scripts. A one-task page must still use this current-page workflow, not the older rejected method.
- If a target review or manual inspection finds a content issue, update the result JSON first, rerun hard checks, then fill and verify again.
