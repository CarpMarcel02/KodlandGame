Dungeon Rush (PGZero)

A fast top-down dungeon crawler built in Python with Pygame Zero. Each run generates a procedural grid of connected rooms. Entering a room locks the doors, spawns enemies, and doors reopen only after you clear the room. Tight movement, solid collisions, directional sprite animations, projectiles for both player and enemies, a simple HUD, plus Game Over and You Win scenes.

Target: small, readable codebase that’s easy to extend (new enemy types, rooms, items).

🎮 Core Gameplay

Controls

Move: WASD

Shoot: Arrow Keys (↑ ↓ ← →) — fires a bullet in the pressed direction

Goal

Clear every room (kill all enemies) to unlock doors and progress.

When all rooms are cleared, you reach the You Win screen.

Health & i-frames

Green HP bar (bottom-left).

Taking damage grants a short invulnerability window to prevent instant meltdowns.

🧠 Systems Overview

Procedural rooms: Rectangular rooms on a grid with real, lockable doors. Player spawns in a safe spot.

Scene manager: menu → play → pause / game_over → you_win.

Entities & AI

SkeletonEnemy — tracks the player, takes attack positions, uses light steering/separation to avoid bunching, damages on contact.

ArmadilloEnemy — winds up briefly, then rolls at high speed (~15s), bounces off walls with slight jitter, pauses (~3s), repeats. Damages on impact only while rolling.

PlantEnemy — static “wall-mounted”; animates and spits projectiles in sync with its “spit” frame; damages on contact too.

Projectiles: team="player" vs team="enemy"; TTL, damage, per-direction sprites, owner.

Collisions & anti-overlap: two passes each frame — push vs player, and symmetric enemy-enemy push (non-pushable entities like plants don’t move).

Rendering & animation: y-sort by rect.bottom for proper top-down layering; DirectionalAnimation for multi-dir sprites; LPC-style sprite sheets.

Audio/UI: background music with Mute button, Pause button (top-right), HP HUD, immediate Game Over (no fade). Player hurt SFX follows the global mute state.

Default spawn logic per room

~2–4 Skeletons, 2–3 Armadillos, up to 4 Plants.

Spawn positions: not in walls/doors, not too close to player, no overlaps.

Win condition

In PlayScene.update(), when a room is marked cleared, check all(state == "cleared"); if true → manager.change("you_win").

Running the Game
Windows (recommended)

Double-click run.bat (provided in repo). It will:

create a virtual environment in .venv/ if missing,

install dependencies from requirements.txt,

run the game with: python -m base_game.main.

Audio & Mute

Background music loops across tracks; Mute toggles music and player hurt SFX.

Add your SFX/music under base_game/sounds and base_game/music.
Use PGZero loaders (e.g., pgzero.loaders.sounds.load("sfx/hurt")).

✨ Extending the Game

Add new enemies by subclassing Enemy and implementing sense/think/move/act.

Introduce new projectile types by extending Projectile (sprites per direction, custom dmg/TTL).

Expand world gen in procgen.py (room shapes, hazards, pickups).

Improve UI: transitions, stats (time, rooms cleared, kill count) on You Win screen.