# Minimal Edit Principle

## Core Rule
Proofreading edits must be strictly minimal. Correct ONLY objective grammar, spelling, punctuation, capitalization, and formatting errors. Do it as lightly as possible.

## What to Correct (Objective Errors Only)
- Spelling errors and typos (e.g. `探套` -> `探讨`)
- Subject-verb agreement violations
- Severe word-order errors that block comprehension
- Wrong homophone usage that changes meaning
- Missing punctuation that creates true ambiguity
- Locale-specific formatting violations (e.g. `。。。` -> `……` in zh-CN)
- Simplified/Traditional character mismatches for the target locale

## What to PRESERVE (Never Change)
- **Semantic content**: no new content, no removed nuance, no shifted emphasis, no unnecessary synonym substitutions
- **Tone, register, style, formality**: do not formalize informal writing or casualize formal writing unless correcting a real error
- **Pronoun referentiality**: preserve person, number, gender features; do not change `您` to `你` in zh-CN
- **Proper noun referentiality**: do not replace or alter names, places, organizations, brands (except grammatical inflection like possessives)
- **Expressivity and colloquialisms**: keep emojis, emoticons, repeated punctuation (`!!!`, `???`), elongated spelling (`soooo`), fillers, internet slang, usernames, hashtags
- **Formatting**: preserve line breaks, indentation, bullet styles, paragraph structure, special symbols, numeric forms, ALL CAPS
- **Local punctuation and formatting**: respect locale-specific quotation marks, punctuation conventions, date/number formats
- **Abbreviations in informal context**: `u`, `r`, `lol`, `btw`, `idk` are intentional in informal text -- do not expand

## Violation = Correctness Penalty
Any edit that violates the Minimal Edit Principle is an **unnecessary edit**. Even one unnecessary edit forces Correctness to `some_unnecessary` (Mixed).

## Key Distinction: Proofreading vs Rewriting
- Proofreading: fixing objective errors while preserving the author's voice
- Rewriting/Paraphrasing: changing wording for subjective improvement
- If the model rewrites instead of proofreading, it violates this principle regardless of whether the rewritten text is "better"

## Exact Repeat Rule
If the input has no objective errors, the only correct response is an **exact repeat** of the input. Any change to error-free text must be evaluated under `alteredMeaning`.
