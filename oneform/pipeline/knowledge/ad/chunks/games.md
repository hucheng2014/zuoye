# Game-Specific Evaluation

## Three Evaluation Dimensions for Games

When the query or advertised app is a game, evaluate relevance using three dimensions rather than just surface-level genre labels.

### Dimension 1: Play Style / Mechanics
How the player interacts with the game. Core gameplay loop.

- Match-3 (Candy Crush, Bejeweled)
- Battle royale (Fortnite, PUBG)
- Turn-based strategy (Civilization, XCOM)
- Real-time strategy (Clash of Clans, StarCraft)
- FPS / shooter (Call of Duty, Halo)
- Puzzle / brain teaser (Sudoku, Wordle)
- Platformer (Mario, Hollow Knight)
- RPG (Final Fantasy, Genshin Impact)
- Sandbox / survival (Minecraft, Terraria)
- Racing (Mario Kart, Asphalt)
- Simulation (The Sims, Stardew Valley)
- Card / board game (Hearthstone, Monopoly)

### Dimension 2: Presentation / Theme
Visual style, setting, narrative tone.

- Cartoon / cute (Angry Birds, Animal Crossing)
- Realistic / gritty (Call of Duty, The Last of Us)
- Fantasy / medieval (Clash of Clans, Diablo)
- Sci-fi / futuristic (Halo, Star Wars)
- Sports (FIFA, NBA 2K)
- Horror (Resident Evil, Five Nights at Freddy's)
- Casual / minimal (Wordle, 2048)

### Dimension 3: Audience / Engagement Level
Who plays this and how deeply.

- Casual (short sessions, simple controls, broad audience)
- Mid-core (moderate complexity, regular sessions)
- Hardcore (deep systems, long sessions, dedicated audience)
- Children-specific (educational, age-gated)
- Social / multiplayer focused
- Single-player focused

## Game Scoring Rules

### Same Game / IP -> Excellent
- Query: "Candy Crush" -> App: "Candy Crush Soda Saga" = **Excellent**
- Query: "PUBG" -> App: "PUBG: New State" = **Excellent**
- Query: "Clash of Clans" -> App: "Clash Royale" = **Excellent** (same IP universe, same developer)

### Strong Competitors (2-3 dimensions match) -> Excellent
- Query: "PUBG" -> App: "Fortnite" = **Excellent** (same play style: battle royale; similar audience: competitive multiplayer; different theme but same genre)
- Query: "Candy Crush" -> App: "Toon Blast" = **Excellent** (same play style: match/puzzle; same audience: casual; similar theme: colorful/cartoon)

### Similar but Not Fully Matching (1-2 dimensions match) -> Good
- Query: "Candy Crush" -> App: "Bejeweled" = **Good** (same play style: match-3; but different franchise, less mobile-focused history)
- Query: "Minecraft" -> App: "Terraria" = **Good** (same play style: sandbox/survival; different presentation: 3D vs 2D)
- Query: "Call of Duty" -> App: "Sniper Elite" = **Good** (same play style: shooter; different sub-genre and tempo)

### Weak Connection (only 1 dimension, loosely) -> Acceptable
- Query: "Candy Crush" -> App: "Angry Birds" = **Acceptable** (both casual mobile games, but different mechanics entirely)
- Query: "racing game" -> App: "Flight simulator" = **Acceptable** (both vehicle-based, different category)
- Query: "FIFA" -> App: "NBA 2K" = **Acceptable** (both sports games, but different sport -- or Good if user searched for "sports game" generically)

### Only "Both Are Games" -> Bad
- Query: "Candy Crush" -> App: "Call of Duty" = **Bad** (no dimension overlap: different play style, theme, audience)
- Query: "chess app" -> App: "Fortnite" = **Bad** (nothing in common except being games)
- Query: "kids educational game" -> App: "Grand Theft Auto" = **Bad** (opposite audience, theme, content)

## Key Principle
Never rate based solely on "both are games." Always evaluate across play style, theme, and audience. The more dimensions that align, the higher the rating.
