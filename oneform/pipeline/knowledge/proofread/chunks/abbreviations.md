# SMS/Slang Abbreviation Preservation

## V2 Core Change from V1
In Proofread V1, abbreviations were generally expanded to standard forms. **V2 reverses this**: abbreviations in informal context must be PRESERVED unless they cause genuine comprehension failure.

## Generally Preserve (Do Not Expand)
- **Internet slang**: `lol`, `lmao`, `omg`, `tbh`, `imo`, `smh`
- **Common abbreviations**: `btw` (by the way), `idk` (I don't know), `fyi` (for your information), `asap`
- **Pronoun shortcuts**: `u` (you), `r` (are), `ur` (your/you're in clearly informal text)
- **Expressive punctuation**: `?!`, `!!!`, `???`, `...`
- **Elongated spelling**: `soooo`, `yessss`, `nooo`, `pleaseee`
- **Emoji and emoticons**: all emoji characters, `:)`, `:(`, `<3`, `^^`
- **Hashtags**: `#topic`, `#mood`
- **Usernames/mentions**: `@username`
- **Technical acronyms**: `API`, `CSS`, `HTML`, `KOL`
- **Units and measurements**: standard abbreviations for units

## When to Expand/Correct
- The abbreviation genuinely blocks comprehension (extremely rare)
- The abbreviation is clearly a speed-writing typo rather than intentional shorthand (context-dependent)
- In **Formal** context, abbreviations may need expansion IF they violate the register

## Scoring Impact
- Model expands `u` -> `you` in informal chat -> **unnecessary edit** -> Correctness = `some_unnecessary`, `unnecessaryEdits: ["abbreviations"]`
- Model removes emoji from informal message -> **unnecessary edit** -> Correctness penalty
- Model normalizes `!!!` to `!` -> **unnecessary edit** -> Correctness penalty (expressivity destroyed)
- Model preserves all abbreviations as-is in informal text -> correct behavior, no penalty

## Reference: Non-Formal Word List
The official guideline appendix provides a detailed word list categorizing abbreviations as "preserve" or "correct." When uncertain, consult this list. The default stance in V2 for informal context is: **when in doubt, preserve.**
