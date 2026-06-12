# Localization

## Purpose
Evaluate whether the poll has locale-specific language, format, or translation issues.

## Options
- `no` — No localization issues
- `yes` — Localization issues present

## Localization Issues (yes)

### Language Mixing
- Poll in zh_CN but title or options contain unnecessary English words
- Conversation is in one language but poll switches to another without reason

### Translation Errors
- Incorrect or awkward translations of conversation content
- Meaning changed or lost through translation

### Punctuation/Format Non-Compliance
- Using Western punctuation in a CJK locale (e.g., comma `,` instead of `，` in zh_CN)
- Date/number formats not matching the locale convention
- Character encoding issues

## No Localization Issues (no)

- Poll language matches conversation language
- Punctuation and formatting follow the locale's conventions
- Proper nouns, brand names, or technical terms kept in their original language (this is acceptable, not a localization error)

## Relationship with Composition
Localization issues may also affect Composition scoring. If a localization problem makes the title or options unnatural or unclear, consider whether Composition should also be marked as `bad`. However, evaluate each dimension independently -- a localization issue doesn't automatically cause a Composition failure.
