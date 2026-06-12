# MEMORY.md
# ASR Annotation — Project Memory Index

## Purpose
This file stores short-running project memory for Docker-based ASR annotation work:
- current working assumptions
- repeated mistakes to avoid
- temporary project state
- recent corrections that should influence future annotations

Do not duplicate full rules already covered in `AGENTS.md`.

## Current Stable Notes
- Task type: audio ASR annotation in Docker container `asr-worker-1-agent`.
- All task-page operations must be container-only through `docker exec asr-worker-1-agent` and the container CDP endpoint.
- Never use host-side Playwright/browser tools for the task page.
- `SC` transcripts must include natural Chinese punctuation, including final punctuation for complete utterances.

## Mandatory Reminder
- [2026-05-12] Local dual-ASR verification is mandatory for every question. The command `/app/_work_context/local_segment_dual_asr.py` must complete successfully for the exact current audio URL and exact segment times before any fill, skip, save, or submit action. If dual ASR fails because of HTTP 403, network errors, empty segments, script errors, missing `tableData`, or any other issue, stop and report the blocker instead of annotating from `remark`, `user_remark`, visible text, or guesswork.
- [2026-05-12] Never use the task page's `自动标注` feature. Recognition and annotation decisions must come only from local dual-ASR output plus manual judgment.
- [2026-05-12] Silent/invalid audio items with no annotatable rows still require local dual-ASR verification. Download the current audio, run dual ASR on the full audio duration, and only submit directly if both models verify silence/no speech.
- [2026-05-12] When a new question arrives, the first priority is local dual-ASR verification of the audio; all other page details are secondary until dual-ASR has completed.
- [2026-05-12] If the audio contains only a very short peak or fragment that clearly cannot support a full utterance, treat it as invalid/silent audio. In that case, either choose the top invalid-audio submission path if the UI provides it, or submit directly without fabricating a transcript.

## Recent Mistakes To Avoid
- [2026-05-12] Mistake: Filled and submitted several ASR annotation questions using `user_remark` after dual-ASR download or page errors. This is not allowed. Dual-ASR success is a hard gate and cannot be bypassed.
- [2026-05-12] Mistake: Clicked the page `自动标注` button while trying to recover empty segments. This is forbidden; if local dual-ASR cannot run, stop and report the blocker instead.
- [2026-05-12] Mistake: Used host-side browser automation for submit once. Future task-page browser control must stay inside Docker/CDP only.
- [2026-05-12] Mistake: Filled a complete Chinese utterance without final punctuation. Future `SC` text must use natural punctuation, for example `好嘞，好嘞。`.
