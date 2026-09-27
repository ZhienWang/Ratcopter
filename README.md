# Ratcopter: Sewer Race — Prompt & Design Log

A running log of every request made for this project and the design decision
made in response, grouped by the date of the commit that shipped it. New
entries are appended here and committed alongside the code change they
describe, so this file's history lines up with `git log`.

Requires Solar2D (https://solar2d.com) to be installed -- the SDK used to be
vendored in `extracted/` and is not in this repo any more. The path below is
a default Windows install; adjust it if yours differs.

Build command:
Remove-Item -Recurse -Force build_output -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force build_output
& "C:\Program Files (x86)\Corona Labs\Corona\Native\Corona\win\bin\CoronaBuilder.exe" build --lua build_html5.lua

Run command:
cd build_output\ratcopter.html5
python -m http.server 8000
---

## 2026-09-11 — commit `c6b4c26` ("decompiled update")

- **"how do i run this corona lab game?"**
  Explained the Solar2D/Corona local run + build workflow.
- **"how can i upload this and make it work correctly in itch.io"**
  Explained itch.io's HTML5 upload requirements (zipped build, embed settings).
- **"can you derive the source code back?"**
  Reverse-engineered `main.lua`/`config.lua` from the compiled HTML5 build
  (`ratcopter.bin`/`ratcopter.data`) by parsing Lua 5.1 bytecode directly and
  resolving decompiler upvalue placeholders back to real variable names.
- **"add a different theme option, add more variations of pipes to be more
  like sewage pipes, change the background to be underground in a sewage
  system."**
  Added a Sewer/Surface theme toggle with a theme button; generated new
  sewer-pipe and underground-background art procedurally (PIL) and wired a
  per-lane theme-application system.
- **"this looks great, push it to itch.io"**
  Clarified scope first (rebuild the real Solar2D game vs. ship the
  decompiled version) — user chose to rebuild the real game.
- **"run it locally"**
  Served the build via a local HTTP server for in-browser testing.

## 2026-09-12 — commit `db6e4e5` ("Updated build")

- **"add a second mirrored screen on the right with an AI playing the same
  game as a race companion. The new goal is now to accumulate the total
  scores in 5 rounds."**
  Added a second, AI-controlled lane racing an identical shared pipe course;
  changed the win condition to total accumulated score across 5 rounds.
- **"center the game, flip the mirrored game on the right side
  horizontally"** / **"the whole gameplay screen is moved down since the
  screen size change, move it up"** / **"why are you not using the screen
  estates on both sides?"** / **"this is not 16:9 ratio, please use the rest
  of the estate, i am not developing for a mobile phone"**
  Multi-round layout/scaling pass: moved from a cramped mirrored layout to a
  true 16:9 960x540 canvas. Asked the user to choose a scaling strategy
  directly rather than keep guessing (they chose fixed 960x540, letterboxed),
  then later reverted to `zoomEven` per "go back to version 17" while keeping
  the AI-lane fix.
- **"the right side screen should be flipped horizontally, not mirrored"**
  Replaced a negative-scale mirror transform (which geometrically reversed
  gameplay direction) with per-image horizontal flips plus an explicit
  position-mirroring function, so art is flipped but layout/motion isn't.
- **"change right side rat to be white"** / **"also make it face the right"**
  Generated a genuinely white bird sprite (grayscale + gamma-curve brighten,
  since Corona's fill-tint can only darken) and stopped flipping just the
  bird image so it faces the same direction as the player's.
- **"ok the AI looks too good, give a delay of each floating action of the
  AI with 100ms"**
  Added a 4-tick (100ms) FIFO delay queue to the AI's control output,
  validated with a standalone Lua simulation before shipping.
- **"the AI needs to feel more human like, such as floating up and down more
  dynamically"**
  Added a sine-wave "bob" to the AI's target altitude. Amplitude (32px) was
  chosen from simulation data showing 28-38px survives every trial while
  45px is frequently fatal.
- **"add right click to short dash forward, this has a cooldown of 2.5
  seconds. the mouse blinks when the cooldown is completed."**
  Implemented a right-click dash with a 2.5s cooldown and a blinking
  indicator dot.
- **"the dash should move the whole screen forward along with the rat, not
  pushing the rat back after"**
  Reworked the dash from a lunge-and-snap-back into a permanent world-shift
  (extra scroll distance under the bird).
- **"stop changing the screen size again"**
  Left `config.lua` untouched from that point on; on later layout-adjacent
  requests, verified the file was unchanged instead of making further
  speculative edits.
- **"the dash needs some transition frames, it shouldn't jump immediately
  forward"**
  Spread the dash's extra distance over a transition window instead of
  applying it instantly.
- **"the dash should be at least 0.7 second longer"**
  Extended the dash transition time to 0.9s.
- **"add some wind animations when i press the dash"**
  Added streak-rect "wind" particles that kick off the bird and fade out on
  dash.
- **"make Z and right arrow to be binded to the Dash"**
  Bound Z and the right-arrow key as additional dash triggers alongside
  right-click.

## 2026-09-13 — commit `8b3a75a` ("Add dash keybinds, AI bob/delay tuning, and lengthen dash distance")

- **"the dash is too short to even pass a single pipe"**
  Increased `DASH_DISTANCE` from 45x to 150x `LANE_SCALE` (~65px → ~218px)
  so a single dash clears a pipe's ~117px collision width with margin. Also
  worked around a CoronaBuilder quirk where `index.html`/`index-debug.html`
  intermittently don't get emitted into the HTML5 build output — fixed by
  restoring the known-good wrapper pages from git rather than regenerating
  them, since they're app-generic and carry no game logic.

## 2026-09-13 — commit `569227d` ("Make dash indicator green when ready, gray on cooldown")

- **"the dash dot UI should be green when you can dash, gray when you
  cannot."**
  Changed the ready-state indicator color from yellow to green, and fixed
  its initial spawn color (previously gray even though the dash starts
  available at the beginning of a round).

## 2026-09-13 — commit `5f20478` ("Add variable pipe spacing")

- **"make the pipes spacing have be variable. But keep the gap right now as
  the minimum gap, so only expand about 20 to 30% per each gaps, once every
  2-7 consecutive pipes."**
  Kept `PIPE_SPACING` as a hard minimum; added a per-course cumulative
  offset array so pipe positions can vary, then made one gap every 2-7
  pipes randomly stretch by 20-30%. Validated with a standalone Lua
  simulation before shipping (confirmed no gap ever drops below the floor
  and wide-gap spacing lands within the intended 2-7 pipe interval).

## 2026-09-13 — commit `4f99cfc` ("Add README.md prompt/design decision log")

- **"create a readme.md to record my prompts and design change decisions
  for every prompts/requests I give. tag the commit date for that log"**
  Created this file as a running project log, backfilled from the full
  request history to date. Going forward, each new request is appended here
  and committed together with the code change it describes.

## 2026-09-13 — commit `c2fefe6` ("Fix dash indicator staying gray after the first round")

- **"fix the dash dot functionality again, the green color is removed"**
  Root cause: `resetLane()` zeroed `dashCooldownRemaining` directly on every
  new round, which bypassed the `>0`-to-`<=0` transition `gameLoop` watches
  for to re-color the dot — so after round 1 the indicator stayed gray from
  then on even though the dash was actually available. `onFlapInput` now
  explicitly resets the indicator to green whenever a round starts (forward-
  declared `setDashIndicatorReady` the same way `tryDash`/`finishRound` are,
  since it's called before its real body is defined later in the file).
  Also reset the indicator's alpha in `setDashIndicatorReady` in case a
  round boundary landed mid-blink, leaving it faded.

## 2026-09-13 — commit `8948b60` ("Give the AI an intentional 15-30% loss chance every 5 pipes")

- **"make the AI have an intentional loss chance of 15%-30% after every 5
  pipes of passing through."**
  Every 5 pipes the AI clears, it rolls a fresh 15-30% chance (randomized
  per checkpoint) to lose right there — forcing the same
  `lane.alive = false` / `rotation = 90` state a real pipe collision
  produces, so it reads as an ordinary crash rather than a scripted event.
  Keeps the AI from just winning every round outright now that its bob/delay
  tuning makes it quite good. Validated the roll logic with a standalone
  simulation before shipping (~22.5% observed per-checkpoint loss rate,
  comfortably inside the 15-30% range, with every death landing on an exact
  multiple of 5).

## 2026-09-13 — commit `6919138` ("Fix nil-global runtime error from AI loss-chance constants")

- **"ERROR: Runtime error / ?:0: attempt to perform arithmetic on global
  'AI_LOSS_CHECK_PIPES' (a nil value)"**
  `AI_LOSS_CHECK_PIPES`/`AI_LOSS_CHANCE_MIN`/`MAX` were declared right
  before `updateAI`, but `updateLane` — the function that actually rolls the
  loss chance — is defined earlier in the file. Lua resolved them as globals
  inside `updateLane`'s closure since the locals weren't in scope yet at
  that point in the file, so they read as nil at runtime. Moved the three
  constants up next to `AI_DELAY_TICKS`, before `updateLane`.

## 2026-09-13 — commit `e4e9b60` ("Make pipes 20% narrower")

- **"make the pipe's width 20% shorter"**
  `PIPE_HALF_W`: 40 → 32 `* LANE_SCALE`. It drives both the pipe sprite's
  rendered width and its collision zone, so shrinking the one constant kept
  the visual and the hitbox in sync automatically.

## 2026-09-13 — commit `e7ab4c5` ("Extract pipe gap formula to gameSetting.csv")

- **"extract the gap formula to a gameSetting.csv where I can adjust it"**
  `randomGapY()` was the hardcoded expression `100 + 20 * math.random(1,
  10)`. Split it into four named values — `gap_base`, `gap_increment`,
  `gap_roll_min`, `gap_roll_max` — loaded at startup from
  `mainGame/gameSetting.csv` (a plain `setting,value` CSV,
  packaged as a normal bundled resource). Falls back to the original
  hardcoded values if the file or an individual key is missing, so a
  malformed CSV can't break the build. Editing the CSV and rebuilding is now
  enough to retune the gap range/step without touching `main.lua`.

## 2026-09-13 — commit `3ece0d8` ("Rename project folder Ratcopter_recovered -> mainGame")

- **"put the gameSetting.csv in root folder"**
  Asked to confirm which "root" was meant: `gameSetting.csv` was already at
  the Solar2D project root (`Ratcopter_recovered/`, alongside `main.lua`),
  and moving it to the outer repo folder instead would stop it from being
  bundled into the build at all. The reply redirected the request: rename
  `Ratcopter_recovered/` itself to `mainGame/`.
  Renamed the folder via `git mv` and updated every path reference to it —
  `build_html5.lua`'s `projectPath`, the two one-off dev scripts
  (`fix_upvalues.py`, `make_bird_white.py`), and the CSV path noted in this
  README — then rebuilt from the new path to confirm the build and
  `gameSetting.csv` packaging still work unchanged.

## 2026-09-13 — commit `fb6cea1` ("Document each setting in gameSetting.csv")

- **"provide comments in the gameSettings.csv on what each variables do"**
  Added a header explaining the file format and the gap formula, plus a
  comment above each of the four settings describing what it controls. The
  Lua loader already ignores any line that doesn't parse as `key,number`, so
  `#`-prefixed comment lines needed no code changes — verified that and
  called it out explicitly in the header, along with the one gotcha: an
  inline comment after a value (e.g. `gap_base,100 # note`) breaks that
  row's parse and silently falls back to the default instead of erroring,
  so comments have to sit on their own line.

## 2026-09-13 — commit `77591ba` ("Extract pipe-to-pipe spacing variation to gameSetting.csv")

- **"I need a pipe to pipe position increment variation setting as well"**
  `nextPipeSpacing()` had the 2-7 pipe interval and 20-30% expansion
  fraction (added earlier for the variable pipe spacing feature) hardcoded
  in `main.lua`. Split into `pipe_spacing_interval_min`/`max` and
  `pipe_spacing_expand_min`/`max`, loaded from `gameSetting.csv` the same
  way as the gap settings — same missing-file/missing-key fallback to the
  original values. Re-validated the resulting spacing distribution with a
  standalone simulation after the change (minimum gap still exactly
  `PIPE_SPACING`, ~22% of gaps widened, matching pre-change behavior).

## 2026-09-14 — commit `a7c7892` ("Add an in-game keybind settings menu")

- **"create a menu where i can change the keyboard bindings"**
  Added a "KEYS" button (top-center, always visible) that opens a panel
  listing the 3 rebindable actions — Flap, Dash 1, Dash 2 (defaults:
  space/z/right) — each with a CHANGE button. Tapping CHANGE puts
  `onKeyEvent` into a "listening" mode where the next keypress anywhere
  becomes that binding; `onKeyEvent` now checks `event.keyName` against a
  `keyBindings` table instead of hardcoded key names. Bindings persist to
  `keybinds.txt` in `DocumentsDirectory` — same save/load pattern as
  `bestscore.txt` — deliberately separate from `gameSetting.csv`, since
  that file is bundled/shipped design tuning, not a per-player runtime
  preference. While the menu is open, a `menuOpen` flag guards every
  gameplay input path (tap catcher, `onKeyEvent`, `tryDash`) and `gameLoop`
  skips updating both lanes entirely, so the player can't die mid-rebind
  and no stray keypress leaks through to flap/dash underneath the menu.

## 2026-09-15 — commit `498b3da` ("Add hold-to-dash option to the keybind menu")

- **"create a checkbox in the keybind to allow Holding the let click to
  dash, it should dash after holding for 0.2 seconds"**
  Added a "HOLD TO DASH" checkbox to the keybind menu, persisted to
  `keybinds.txt` alongside the key bindings. When on, a left click starts a
  200ms timer instead of flapping immediately: released early, it flaps as
  a normal tap; held past 200ms, `tryDash()` fires instead and the eventual
  release is swallowed so it doesn't also flap. `tryDash()` now returns
  whether it actually dashed, so a click held past 200ms while dash is on
  cooldown still falls back to a flap on release instead of doing nothing.
- **"change text to Hold to Dash, then add Space to the Left click hold"**
  Renamed the checkbox label and extended the same hold-vs-tap timer to the
  flap key (default space) via `onKeyEvent`'s "up" phase, which the handler
  previously ignored entirely. Guarded with a `menuOpen` check and a
  `flapKeyHeld` flag so OS key-repeat can't re-arm the timer and releasing
  the key while the keybind menu happens to be open can't sneak in a flap.

## 2026-09-15 — commit `8eb0363` ("Make the hold-to-dash delay adjustable via a slider")

- **"make the hold timer to be adjustable in the UI with a slider."**
  Replaced the fixed 200ms `HOLD_DASH_DELAY_MS` constant with a
  `holdDashDelayMs` variable (50-600ms range), persisted to
  `keybinds.txt` the same way as the other keybind-menu settings. Added a
  draggable slider row below the "HOLD TO DASH" checkbox -- a track plus
  handle that respond to Solar2D's "touch" event (which mouse drags
  already generate, same as every other control in this menu), snapped to
  the nearest 10ms, with a live value readout (e.g. "0.20s"). Enlarged the
  keybind panel to fit the new row without overlapping the existing ones.

## 2026-09-15 — commit `d7f4af5` ("Add cross-lane steal-dots mini-game")

- **"add an interaction where random dots are spawned in the game, when a
  mouse eats it, it transfers to the other side. If the other mouse eats
  that same transfered dot, they lose a point"**
  Added a steal-dot mini-game: every 3.5-7s a dot spawns into a random
  lane and scrolls in like a pipe. The first bird to touch it ("fresh",
  rendered with the previously-unused `gold.png`) gains nothing directly --
  it despawns and an identical "marked" dot (`silver.png`) spawns into the
  OTHER lane instead, riding in the same way. If that lane's bird touches
  the marked dot too, it loses a point (floored at 0); dodging it just lets
  the exchange fizzle with no effect. Transfers are queued
  (`pendingDotTransfers`) and resolved in `gameLoop` rather than inside
  `updateLane`, since `updateLane` is defined earlier in the file than
  `playerLane`/`aiLane` exist as locals -- referencing them directly there
  would silently resolve as globals, the same pitfall `AI_LOSS_CHECK_PIPES`
  hit previously (see the 2026-09-13 `6919138` entry above).

## 2026-09-15 — commit `707ce8f` ("Spawn steal-dots in the gap between pipes, not near them")

- **"don't spawn the dot/coin near the pipes, spawn it in between the
  pipes"**
  `spawnDot` previously dropped a dot at a fully random position (fixed
  spawn x matching the pipes' own off-screen spawn point, fully random y),
  which could land near or visually overlap a pipe. It now sorts the
  lane's three tracked pipes by x and spawns at the midpoint between two
  neighboring ones -- since `PIPE_SPACING` is much wider than a pipe's own
  `PIPE_HALF_W`, that keeps the dot clear of both regardless of y, instead
  of landing on top of one. Only a gap whose midpoint is still ahead of
  the bird is eligible, so a dot can't land on an already-passed gap and
  spawn instantly uncatchable (or appear to pop in behind the bird); if
  neither of the lane's two gaps qualifies at that moment, it just spawns
  nothing and the next timer roll tries again.

## 2026-09-15 — commit `9a346e6` ("Let the bird sink halfway into the ground before dying")

- **"allow the rat to drop half way through the bottom of the screen before
  it loses, right now it's using the ground as the death"**
  `GROUND_LIMIT` was pinned to the ground art's top edge, so death
  triggered the instant the bird touched the surface. It's now the
  vertical midpoint of the ground strip instead (`LAND_TOP` plus half the
  strip's own height), so the bird visibly sinks partway into the dirt
  before losing. Hoisted the ground strip's height fraction (0.19,
  previously a literal duplicated wherever it was needed) into a shared
  `LAND_HEIGHT_FRACTION`/`LAND_TOP` so the land art in `buildLaneVisuals`
  and this death line can't drift out of sync. Also re-clamped the
  steal-dot spawn range to `LAND_TOP` (the actual ground surface) rather
  than the new deeper `GROUND_LIMIT`, so dots don't start spawning inside
  the dirt now that the two no longer mean the same height.

## 2026-09-17 — commit `TBD` ("Make coins generate the opponent's pipes instead of moving points")

- **"change the dot interaction in the game to no longer minus or give
  points, make it to generate a pipe after 1 second delay of the opposite
  team earning the coin. pipes don't spawn automatically, keep the spawning
  gap rules. If player earns the coin, generate the pipe on the AI screen.
  Make coin spawns 3 times more often."**
  This inverts where obstacles come from, so it touched both halves of the
  steal-dots feature and the pipe course underneath it.

  *Coins.* The two-stage fresh/marked exchange is gone, and with it the
  silver "marked" dot (`Assets/silver.png` is now unreferenced) and every
  score change a dot could cause. There is one kind of coin, it is always
  gold, and collecting it neither adds to nor subtracts from the
  collector's score -- it queues an attack on the other lane instead.
  `DOT_SPAWN_MIN/MAX_INTERVAL` are written as a division of the original
  window rather than as pre-divided literals, so the multiplier stays
  visible in the source.

  *The 1-second delay.* Collecting a coin pushes `{from = lane, remaining =
  COIN_PIPE_DELAY}` onto `pendingPipeSpawns`, which `gameLoop` ticks down by
  `TICK_DT` each frame and drains into `spawnPipe(otherLane(...))`. That
  countdown deliberately rides the game's own tick rather than
  `timer.performWithDelay`, so a pending pipe freezes along with everything
  else while the keybind menu is open and is dropped cleanly on a round
  reset, instead of firing into a lane that has since been rebuilt. The
  queue keeps the same cross-lane indirection the old transfer queue needed:
  `updateLane` is defined before `playerLane`/`aiLane` exist as locals, so
  it can't resolve "the other lane" itself without silently reaching for
  globals (the pitfall `AI_LOSS_CHECK_PIPES` hit previously).

  *Pipes on demand.* The shared course (`courseGaps`/`courseImages`/
  `courseCumOffset`/`ensureCourse`) and the three recycled pipe slots per
  lane are gone. `lane.pipes` is now a plain list that starts empty every
  round; `spawnPipe` creates one display object on demand and `updateLane`
  destroys it once it passes `simX < -60` instead of recycling it forward.
  The two lanes consequently no longer fly an identical course -- each
  side's obstacles are whatever the opponent earned for it, which is the
  point of the change. Pipes get their own `lane.pipeGroup`, inserted
  between the land and the bird in `buildLaneVisuals`, purely for z-order:
  pipes are created at arbitrary times now, and dropping each one straight
  into the lane group would stack it above the bird and the score text
  rather than behind them.

  *The gap rules are unchanged.* Gap heights still come from `randomGapY()`
  (the `gap_base`/`gap_increment`/`gap_roll_*` settings), and consecutive
  pipes in a lane still sit no closer than `PIPE_SPACING` with one gap in
  every `pipe_spacing_interval_min..max` stretched by
  `pipe_spacing_expand_min..max` -- `spawnPipe` places a new pipe a full
  `nextPipeSpacing()` behind the lane's current rightmost pipe whenever that
  already sits past the normal off-screen spawn point, so a lane fed a burst
  of coins queues its pipes up at proper spacing instead of stacking them.
  Since spawns are driven by each lane's own coin traffic rather than one
  shared course, the "pipes until the next stretched gap" counter became
  per-lane state (`lane.pipesUntilWideGap`).

- **"make the coins spawn 5 times more often"**
  Followed a playtest of the 3x rate above: with pipes arriving only from
  coins, a lane was getting a pipe roughly every 10-12 seconds, and two
  full 5-round matches finished 0-0 because neither bird met enough pipes
  to clear one. The window went to a 0.70-1.40s roll against the original
  3.5-7.0s. Read as 5x the original rate, not 5x the 3x one -- stacking
  them would have meant a coin every quarter second.

- **"put the coin spawn rates in the gamesettings.csv"**
  `coin_spawn_interval_min`/`_max` join the gap and pipe-spacing settings,
  so the coin rate -- which is now also the obstacle rate, since nothing
  else spawns pipes -- is tunable without a code edit. Two things had to
  move for it. The `loadGameSettings`/`settingOrDefault` block was declared
  *below* the coins section, so it was lifted above it: the coin rate is
  now the earliest constant that reads the CSV. And `DOT_SPAWN_MAX_INTERVAL`
  is clamped up to the min rather than trusted as read -- unlike a bad
  `gap_roll_min`/`max` pair, which makes `math.random` throw loudly at
  startup, a max below the min would have `rollNextDotSpawnIn` return
  negative waits and silently spawn a coin every single tick.


- **"create an animation and a sound when the coin is earned by the player,
  the animation should show the coin bouncing to the right edge of the AI's
  screen, and thus generating the pipes, this is similar to sending garbage
  in Tetris. Do the same for the AI side."**
  The collected coin no longer just disappears. It is lifted out of the lane
  at the exact point it was taken and bounces across to the right edge of the
  opposing lane -- the spot that lane's pipes scroll in from -- and the pipe
  is generated at the instant it lands. The flight lasts `COIN_PIPE_DELAY`,
  so the animation *is* the one-second delay rather than something layered
  on top of it, and both directions animate: your pickup flies right into
  the AI's lane, the AI's flies left into yours.

  *Where it lives.* Each lane's frame is a `display.newContainer`, which
  clips its contents -- a coin animated inside `lane.group` would simply be
  cut off at the lane edge and never reach the other side. Flights ride in a
  top-level `coinFlightGroup` created immediately after the lane frames and
  the divider (so above them, below every HUD element built later), with
  `laneScreenX`/`laneScreenY` converting out of lane-local space.

  *The arc.* `updateCoinFlight` runs x straight across while y falls toward
  the ground line with a decaying `|sin|` lifting it into
  `COIN_FLIGHT_HOPS` successively smaller arcs, plus two full rotations on
  the way. The arc term is zero at both t=0 and t=1, so the ends stay exact:
  it leaves from the pickup point and arrives at the target, no drift.

  *Sound.* `boomSound` was loaded at startup but had never been played by
  anything; it is now the launch sound, and it fires for the AI's pickups
  too rather than only the player's -- being sent a pipe should be as
  audible as sending one. (It is also, incidentally, the only sound that
  survives a browser: the other five are `.caf`/`.aif`, which Chrome refuses
  to decode, while `sfx_boom.mp3` plays.)

  *Lifecycle.* The flight rides the game's own tick alongside the payoff it
  belongs to, so it freezes with everything else when the keybind menu is
  open. `clearPendingPipeSpawns` replaced the bare `pendingPipeSpawns = {}`
  at round start so an in-flight coin is destroyed rather than stranded
  mid-screen when a round ends under it.


- **"make the coin sound softer and it should repeat whenever a coin is
  earned"**
  Channel 1 is now reserved (`audio.reserveChannels`) for the coin launch
  alone and set to `COIN_SOUND_VOLUME` = 0.3, against 1.0 for every other
  effect. Reserving matters for both halves of the request: every other
  `audio.play` in the file auto-allocates a channel, so without the
  reservation the quieter volume would eventually land on the flap, point
  and hit sounds too.

  The repeat comes from `playCoinSound` stopping the channel before
  replaying it. `audio.play` on a channel that is still sounding is refused
  outright rather than queued, and at a 0.7-1.4s coin rate across two lanes
  a second pickup inside the previous sound's length is routine -- so
  without the stop those pickups would be silent. Confirmed by removing the
  stop and watching three back-to-back pickups produce zero plays instead of
  three. Each earn now retriggers a clean, distinct hit rather than stacking
  another overlapping copy.


- **"change to elimination based game over rule, AI and Player should stop
  when the other player loses"**
  A round now ends the instant either bird goes down, and the survivor
  freezes where it stands. `gameLoop`'s death handling collapsed to a single
  `if not playerLane.alive or not aiLane.alive then finishRound() end` --
  leaving the "playing" phase is what stops both lanes, since nothing calls
  `updateLane` outside that branch.

  *What went away.* The whole `spectating` phase: the player crashing used
  to leave the AI flying on, with a top banner ("YOU CRASHED -- WATCHING
  AI") and a tap-to-skip path in `onFlapInput` that called `finishRound`
  early. None of that is reachable under elimination, so the phase, its
  banner, its text object and both branches are gone rather than left as
  dead code. The reverse case was even quieter: an AI crash used to do
  nothing at all, letting the player keep scoring against a frozen lane.

  *What the summary says.* The round overlay leads with the outcome --
  "AI ELIMINATED" / "YOU WERE ELIMINATED" / "BOTH ELIMINATED" -- with the
  scores demoted to the subtitle, since what ended the round is now the
  headline rather than the score. `match.eliminated` is set in
  `finishRound`. "Both" is a genuine outcome, not a tidy default: the AI's
  handicap roll fires inside `updateLane` while it scores a pipe, which can
  be the same tick the player hits something.

  *Balance consequence.* The AI's deliberate-loss handicap (a 15-30% roll
  every 5 pipes) now hands the round straight to the player instead of
  merely ending the AI's own run, so it is a considerably bigger gift than
  it was. Match scoring is still cumulative pipes over 5 rounds rather than
  rounds-won, which is worth revisiting now that each round has a clear
  winner.


- **"in mobile phone, the dash won't work"**
  Two independent causes, both of which had to go.

  *No touch path to the dash.* All three dash inputs were pointer- or
  keyboard-only: `Runtime "key"` (Z / right arrow), `Runtime "mouse"`
  (right-click), and the hold-to-dash timer, which was armed *only* inside
  those two handlers. Touch reached the game through exactly one listener --
  `tapCatcher`'s `"tap"` -- which only ever flaps. So a phone had no way to
  dash at all. Added `dashButton`: a finger-sized rounded rect behind the
  DASH indicator and its label (neither has a listener, so a tap on the
  cluster falls through to it), sized against the visible content width and
  floored for thumbs. It fires from `"touch"` on press rather than `"tap"`,
  because returning true to stop the press also reaching the tapCatcher --
  necessary, or the tapCatcher's hold timer arms, fires a second dash and
  leaves `holdDashSuppressTap` set, eating the next genuine flap -- also
  stops Corona synthesising a `"tap"` for that object, so a tap listener
  alone never ran. Also added the touch mirror of the mouse hold-to-dash
  timer, so that option works on a phone instead of silently doing nothing.

  *The HUD was off-screen anyway.* Even with a dash control, it wasn't
  reachable: the whole layout sat ~86px left of the real viewport. `main()`
  was deferred a single frame, which the file's own header already flagged
  as necessary on HTML5 -- but one frame isn't enough in a mobile browser.
  The canvas was measured stepping `300x150 -> 412x618 -> 412x880` over the
  first second, so the layout was built against the middle reading, and
  everything anchored to `SCREEN_LEFT` (the BEST label, the dash control)
  slid off the edge. Boot now polls until `actualContentWidth/Height` stop
  changing (3 consecutive identical reads, 3s cap) before running `main()`.
  Verified by driving a real touch context: the dash fires at 412x880 and at
  1280x820, and the HUD sits fully inside the phone viewport.

  *Left undone.* The keybind menu panel is a fixed 460 content units wide
  and a portrait phone shows only ~253, so the menu -- the HOLD TO DASH
  toggle included -- is partly off-screen and untappable there. The touch
  hold-to-dash path itself is confirmed working (enabled through the menu by
  touch at 1280x820, then a press-and-hold fired the dash); it is only the
  menu's own width that a phone can't reach. Nothing else repositions on a
  later resize either, so rotating mid-game still breaks the layout.


- **"now it fails to load on mobile but not desktop" / "it says failed to
  load .bin file"**
  Two separate things, only one of which is ours.

  *The live failure is itch-side.* "Failed to load .bin file" is the alert
  in the Corona HTML5 bootstrap when the XHR for `ratcopter.bin` doesn't
  come back successfully. On the live page it doesn't: itch's CDN returns
  **404 for `ratcopter.bin`** on every build pushed in the last hour
  (1995439, 1995460, 1995467) while older builds (1995255, 1990605) still
  serve it at 200. It is not a content problem -- 1995467 was pushed with
  the stock, untouched `index.html` restored from git and 404s just the
  same. itch does appear to publish these builds file by file (1995467's
  `ratcopter.data` flipped to 200 while its `.bin` stayed 404), so this
  reads as a stuck or very slow publish rather than a rejected upload.
  Pushing again only creates more unserved builds, so stop after one.

  *A real latent loader bug, found on the way.* The bootstrap accepts the
  download only `if (this.status == 200 && this.response)`. itch sits behind
  Cloudflare, which advertises `Accept-Ranges: bytes` and answers ranged
  requests with **206 Partial Content** -- confirmed with curl against the
  live file. A 206 carries the complete body but fails that check, so the
  loader alerts. Desktop issues a plain GET and never sees it; mobile
  browsers routinely do not. Forcing the status in a browser reproduces it
  exactly: 200 loads, 206 gives precisely "Failed to load .bin file" with
  the canvas stuck at its 300x150 default. Replaced the check with
  `binResponseComplete()`, which takes 200/206/0, and rejects a genuinely
  short body by comparing `response.byteLength` against the total in
  `Content-Range` -- verified all three ways (200 loads, full 206 loads,
  truncated 206 refused). Note this is *not* what is breaking the live site
  today, so it stands as a robustness fix rather than a confirmed cure.
  It has to be re-applied after every build: CoronaBuilder fails to
  regenerate `index.html` (the splash-template error), so that file comes
  from git and the patch does not survive a `git checkout` of it.

  *Boot poll hardened.* The stability poll added earlier could latch onto
  the canvas's 300x150 default -- perfectly stable for the first few hundred
  milliseconds -- and lay out against the placeholder, the very thing it
  exists to avoid. It now also requires `LAYOUT_MIN_WAIT_MS` (400ms) to have
  passed before accepting any reading.

  *Knock-on fixes.* `spawnDot` used to require an open gap between two of
  the lane's three guaranteed pipes and spawn nothing when none qualified;
  a lane now routinely holds zero or one pipe, so that fallback would have
  starved coins exactly when the lanes were emptiest. It still prefers a
  midpoint between two pipes ahead of the bird when one exists, and
  otherwise rides the coin in from the usual off-screen spawn point. Pipes
  and coins are placed by independent spawners now rather than coins being
  slotted into a course the pipes already defined, so both run their
  position through `pushClearOf` against the other kind of object --
  without it, a coin and a pipe spawned into an empty lane a second apart
  would ride in on exactly the same spot. `updateAI` iterates the dynamic
  pipe list and already had a no-target fallback, so the AI simply holds
  its resting altitude (with the usual bob) whenever the player hasn't fed
  it a pipe lately; that band overlaps most of the coin spawn range, which
  is what keeps the AI collecting coins and so keeps the player supplied
  with pipes in return. `applyThemeToLane` re-rolls each lane's own live
  pipes on a theme swap, since there is no longer a shared skin list to
  keep the two sides in sync.

## 2026-09-21 — commit `TBD` ("Fix round-end freeze, coin z-order and stacking, and a latched flap-eating flag")

- **"try to find and fix bugs on your own"**
  A read of the whole file plus a headless run of it. There is no way to
  execute Solar2D here, so the game was driven through a stub of the
  `display`/`audio`/`timer`/`system`/`Runtime` APIs: display objects become
  plain tables recording what the game writes to them, and a virtual clock
  drives `timer.performWithDelay`, so `main.lua` runs unmodified. Every fix
  below was confirmed the same way -- reproduced against a copy of the file
  with that one fix reverted, then shown gone -- over an 84-round soak
  (~1000 seconds of play) that also turned up no runtime errors and no
  display-object leak across round resets.

  *The round did not actually freeze.* `gameLoop` gated the lanes on
  `match.phase == "playing"` but ran the coin-payoff pass unconditionally,
  so after a crash the queued coins kept bouncing across the game-over
  overlay and their pipes were still generated into two frozen lanes --
  contradicting the elimination rule's own "the survivor freezes exactly
  where it was". The phase check is now an early return covering the whole
  tick, and `finishRound()` returns rather than falling through into the
  payoff pass on the tick it ends the round. The soak saw six pipes spawned
  under the overlay before the fix and none after. What is still queued now
  freezes in place the way it already did for the keybind menu, and is
  destroyed by `clearPendingPipeSpawns` at the next round.

  *Coins drew over the bird and the HUD.* `buildLaneVisuals` created
  `lane.pipeGroup` specifically so pipes would sit behind the bird and the
  score, but `spawnDot` still dropped coins straight into `lane.group`,
  which puts them above everything built after it -- and a coin can sit as
  high as `CEIL_LIMIT`, level with the score readout. Coins get their own
  `lane.dotGroup` inserted just after the pipes', so they draw above pipes
  and behind the bird, the score and the lane label.

  *Two coins could land on exactly the same spot.* `spawnDot` ran
  `pushClearOf` against the lane's pipes but never against its own coins, in
  either branch. The soak caught a pair at 0.0 px apart: one had ridden in
  from off-screen, and 1.2s later a second was placed at a between-the-pipes
  midpoint that happened to be exactly where the first had scrolled to. Two
  coins drawn as one, collected by a single pass, sending two pipes for one
  visible pickup. A midpoint is now rejected outright if a coin is already
  near it (`isClearOf` -- nudging it right would shove it through the pipe
  the midpoint was measured from), and the off-screen fallback clears coins
  as well as pipes. `pushClearOf` takes several lists for that, since
  clearing them one at a time could undo the previous pass.

  *A held press could eat the next flap.* `holdDashSuppressTap` is set when
  hold-to-dash fires from a held press, and cleared by the release's `"tap"`
  -- but that tap does not always reach the handler that clears it. The
  theme and KEYS buttons carry a `"tap"` listener and no `"touch"` one, so a
  press on either still reaches the `tapCatcher` underneath and arms its
  hold timer, while the release's tap is claimed by the button. Holding
  either with hold-to-dash on therefore left the flag set and swallowed the
  next genuine flap. Both press paths (touch `"began"` and primary mouse
  down) now clear it, which is safe because the tap belonging to a press is
  always delivered before the next press starts.

  *Two smaller ones.* The coin's ground clamp pinned its *centre* to
  `LAND_TOP`, which still buried the bottom half of the sprite in the dirt
  the clamp exists to avoid; it is now half a coin above the surface. (With
  the shipped `gameSetting.csv` the clamp is never actually reached -- the
  gap formula tops out at 320 -- so this is a latent path that a different
  `gap_base`/`gap_increment` would expose.) And `gameLoopTimer` was the
  file's one accidental global, now a local like `layoutWaitTimer`.

  *Found and left alone.* Holding the theme or KEYS button with hold-to-dash
  on still *fires* a spurious dash -- the fix above only stops it eating the
  following flap. Closing that needs those buttons to consume the press,
  which per the `dashButton` comment also suppresses the synthesised tap
  they currently rely on, so it is an input-plumbing change rather than a
  one-liner. `flapKeyHeld` can also latch on if the flap key's `"up"` is
  lost to a focus change mid-hold, leaving the key dead until a click
  restores it. Five of the six sounds are still `.caf`/`.aif` and so silent
  in a browser; converting them needs an encoder that is not available here.
  And the fixed-width overlay (640 units) overflows a narrow viewport the
  same way the keybind panel already does.

  *Not rebuilt.* `build_output/` still holds the 2026-09-19 build, so none
  of this is in the shipped HTML5 yet.

## 2026-09-24 — commit `TBD` ("Drop the native iOS/Android target and its assets")

- **"since this is an HTML project now, help me remove the mobile version"**
  Scoped first, because "the mobile version" reads two ways here: the native
  app build, or the game's own touch/phone-browser support. The choice was
  the former only -- the web build still has to work on a phone browser, so
  `main.lua` was not touched at all. The DASH button, the touch mirror of
  the hold-to-dash timer and the boot-time layout poll all stay exactly as
  they are. (The poll in particular is not really mobile-specific: a desktop
  browser can also report a transient canvas size on the first frame, which
  is what the file's original header comment already warned about.)

  *What went.* Everything that only ever fed an App Store / Play Store
  build, all of it tracked in git and so recoverable:
  `LaunchScreen.storyboardc/` (the iOS launch screen), `Icon-150.png`,
  `Icon-278.png` and `Assets/Icon-1024.png` (app icons), the sixteen
  `widget_theme_*.png` files, and the `plugin.vk.direct` pair
  (`plugin_shim/plugin_vk_direct.lua` and `plugin_vk_direct_js.js`).
  Roughly 1 MB, none of it reachable: the widget themes back Solar2D's
  `widget` library, which this game never requires, and nothing in the
  project requires the vk shim either -- it came with the original
  decompiled Corona project and has been dead since. Two of them were still
  being packed into the shipped `ratcopter.data`.

  *What `build.settings` says now.* The `android` and `iphone` sections, the
  `LaunchScreen`/`Images.xcassets` references (the latter pointing at a
  directory that does not exist) and the `plugin.vk.direct` entry are gone,
  which also stops CoronaBuilder fetching a plugin the game never calls. The
  portrait `orientation` lock went with them: the game is a 16:9 landscape
  canvas and demonstrably never honoured that setting, so it was a
  contradiction rather than a constraint -- worth a look on the next build
  all the same, since it is the one removal whose effect can only be
  confirmed in a browser. Canvas size and scaling were never in this file;
  they live in `config.lua`.

  *Checked, not assumed.* Every `Assets/`, `Sounds/` and bundled-data path
  `main.lua` can hand the runtime was resolved against the tree afterwards
  (21 of them, all literals -- nothing builds a path at runtime): all still
  present. The headless harness from the previous entry was re-run over 84
  rounds with no change in behaviour.

  *Left alone.* `Assets/` still carries art the current game never draws --
  `silver.png` (orphaned when the steal-dot exchange became coins),
  `bird1.png`, `board.png`, `button.png`, `gameover.png`, `getready.png`,
  `habra.png`, `pipeDown.png`, `pipeUp.png`. That is unused-asset cleanup,
  not mobile removal, so it was out of scope here.

  *Not rebuilt.* `build_output/` still holds the 2026-09-19 build, so
  neither this nor the previous entry's fixes are in the shipped HTML5 yet.

## 2026-09-24 — commit `TBD` ("Purge the vendored Solar2D SDK from the repo and its history")

- **"remove the extracted as well"**
  `extracted/` was 692 MB of vendored toolchain and working scrapings: the
  Solar2D SDK itself, the 213 MB installer `.msi` it came from, 61 MB of
  install logs, `butler/` for itch.io pushes, the `unluac.jar` decompiler
  and its `source/`/`lua_bin/`/`gen/` output from the original
  reverse-engineering, the previous build's `coronaHtml5App.js`/`.mem`, and
  a pile of debug screenshots and probe dumps. All of it tracked in git.

  *Two things were worth saying before deleting.* It held the only Solar2D
  on this machine -- nothing under `Program Files` -- so removing it means
  no builds until Solar2D is reinstalled from solar2d.com. And because it
  was tracked, deleting the files would not have shrunk the repository at
  all: git keeps every blob in history, so a clone would still have pulled
  the full 451 MB `.git`. Reclaiming that needs a history rewrite, which is
  what was chosen.

  *What happened.* The repo was copied whole to
  `../Ratcopter-backup-2026-09-24` first (verified: 34 commits, `extracted/`
  intact, all 52 uncommitted paths preserved). `extracted/build_html5.lua`
  -- the CoronaBuilder parameter file, and the one piece of actual project
  config in there -- was `git mv`'d to the project root. Then `extracted/`
  was deleted, the working tree committed, and
  `git filter-repo --path extracted/ --invert-paths` run over all 34
  commits on both branches.

  *Build command changed.* It pointed into the vendored SDK
  (`.\extracted\Solar2D_extracted\...\CoronaBuilder.exe`) and now points at
  a default Solar2D install under `Program Files (x86)`, with `--lua
  build_html5.lua` reflecting the file's new home. `build_html5.lua`'s own
  `dstPath`/`projectPath` are absolute and were already correct, so they
  are untouched.

  *A .gitignore, finally.* The repo had none. It now ignores `extracted/`
  (so a reinstalled SDK unpacked there is never committed again),
  `build_output/` and `*.zip`. The latter two are noted in the file as
  already-tracked from earlier commits -- `.gitignore` only governs
  untracked paths, so those rules do nothing until
  `git rm -r --cached build_output *.zip` is run. Left for a separate
  decision, since dropping `build_output/` means the repo no longer carries
  a playable build.

  *Not pushed.* The rewrite is local only. Every commit hash on `main` and
  `testing-new-obstacle-throwing-pipes` has changed, so publishing it to
  `github.com/ZhienWang/Ratcopter` needs a force-push, which breaks any
  existing clone or fork. filter-repo also drops the `origin` remote on
  purpose to prevent an accidental one; it has to be re-added by hand.
