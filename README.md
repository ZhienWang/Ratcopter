# Ratcopter: Sewer Race — Prompt & Design Log

A running log of every request made for this project and the design decision
made in response, grouped by the date of the commit that shipped it. New
entries are appended here and committed alongside the code change they
describe, so this file's history lines up with `git log`.

Solar2D is no longer installed, so there is no CoronaBuilder build any more.
`tools/repack_html5.py` updates the last HTML5 build in place instead: it
compiles `main.lua`/`config.lua` to the runtime's 32-bit Lua 5.1 bytecode and
swaps them, the art and `gameSetting.csv` into the existing package, keeping
the wasm runtime as it is. Needs Python with `lupa` and `Pillow` installed.

`build_output/` is gitignored, so the build there is not in history.
`ratcopter-web-current.zip` (2026-09-19) is the last CoronaBuilder build and
the base the repack was first applied to; unzip its `.bin`/`.data` over
`build_output/ratcopter.html5/` to start from it again.

Build command (run from the repo root):
python tools/repack_html5.py

Run command (from the repo root; serves with caching off -- see
tools/serve.py for why plain `python -m http.server` can show a black screen):
python tools/serve.py

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

## 2026-09-26 — commit `TBD` ("Add pipe shapes, slow-closing clamps, and a per-round difficulty ramp")

- **"do your best to create 5 more different settings for the game, add
  different shapes of pipes, such as a triangle, half moon, pentagon, etc,
  also add a moving one the clamps, but clamps really slowly"**

  *Pipes became two jaws.* A pipe used to be one 100x1000 image with a hole
  painted through the middle, which meant the opening was fixed the moment
  the art was drawn. It is now a display group holding a top jaw and a bottom
  jaw, positioned either side of an opening the game decides at runtime --
  which is the whole reason a clamp can close. The group's own `y` still
  doubles as the centre of the opening, so `updateAI` and `spawnDot`, which
  both read `p.y`, needed no change.

  *Shapes are art, not just hitbox.* `tools/make_pipe_shapes.py` generates
  16 jaw images (4 skins x 4 shapes) into `mainGame/Assets/`, rebuilding each
  jaw from its source pipe's own gradient and rim so the new shapes sit next
  to the original art rather than beside it. Every pipe body turned out to be
  the same horizontal gradient repeated down the image, which is why a jaw of
  any height can be rebuilt from one sampled row. The four whole-pipe images
  are kept as that script's source. The set is 37 KB in total -- a gradient
  compresses to almost nothing.

  `shapeNotchPx()` in main.lua mirrors `notch_at()` in the generator: a
  triangle tapers linearly to a point, a half-moon follows a circle, a
  pentagon holds a flat band across the middle 45% and chamfers out. Depth is
  scaled per shape so the broader the tight stretch, the shallower the bite,
  or the pentagon would be far crueller than the triangle at the same number.
  Both run the profile across the *painted* 63% of the image width rather
  than the full hitbox, so a triangle comes to its point at the edge of the
  pipe you can actually see.

  *The clamp.* Flat jaws that squeeze together as the pipe comes at you.
  Always flat and always two-jawed: a shaped tip on a closing opening stacks
  two narrowings and can leave nothing to fly through. Its countdown runs
  only while the pipe is on screen, so one queued up behind a burst of coins
  does not arrive already shut.

  Testing caught the close time being wrong. At the first-guess 4.0s a pipe
  is only on screen for about 3.6s, so a clamp could never finish closing and
  `clamp_gap_min` was unreachable -- the harness proved it by never once
  observing the floor. 2.5s closes visibly the whole way across and is about
  85% shut at the moment you fly through it.

  *The AI needed telling.* Its bob was a flat 32px, tuned against a 50px
  half-opening, and 32px of wander inside a triangle's 30px pinch is a
  guaranteed crash. The amplitude is now the same *share* of whatever the
  pipe being flown at actually leaves open, so it tracks shapes, clamps and
  `pipe_gap_half_height` alike.

  *Five settings*, plus `pipe_gap_half_height` promoted out of a hardcoded
  50 to be the reference the rest are measured against:
  `pipe_shaped_chance`, `clamp_pipe_chance`, `clamp_close_time`,
  `clamp_gap_min`.

- **"make the pipes to only have a single pipe in the beginning, then
  gradually gets two pipes on the same column, but with wider gaps, then it
  becomes smaller at around 2 minutes mark. At 0-30 seconds, there should
  only be one pipe."**

  Asked two things first, because both readings were live. "A single pipe"
  turned out to mean one jaw per column -- hanging from the ceiling or
  standing off the floor, with open lane past it to fly round -- rather than
  splitting the existing gap in two with a middle block. And the ramp runs on
  a clock that restarts every round, chosen over total match time with the
  trade-off stated: a round ends the instant either bird crashes, so at the
  ~16s rounds the harness sees, the later eras are rare. That is visible in
  the numbers -- a 64-round run built 310 one-pipe columns against 2
  two-pipe ones. Lower the thresholds in `gameSetting.csv` to bring the rest
  of the curve into reach.

  *Three eras*, all tunable: one jaw only for the first 30s; two-jaw columns
  mixed in with increasing likelihood until 90s; the opening closing from
  1.35x the base gap down to 0.85x between 120s and 180s.

  A one-jaw column is placed by its *edge* rather than by a gap centre, so
  the lane it leaves open is a known size -- at least four times the half-gap
  -- instead of whatever `randomGapY` happens to give once the ramp has
  scaled things. `laneCollides` only tests the jaws a column actually has,
  and `pipeAim` hands the AI the middle of the open lane rather than a gap
  centre that does not exist. Coins moved onto the same aim point: averaging
  two `p.y` values put them inside a jaw for one-pipe columns.

  *Six more settings:* `ramp_single_pipe_until`, `ramp_two_pipe_by`,
  `ramp_tighten_at`, `ramp_tighten_by`, `ramp_gap_wide`, `ramp_gap_tight`.

  *A wall worth recording.* Adding all of this hit Lua's hard ceiling of 200
  locals per function -- everything in this file lives inside `main()` -- and
  the compile failed pointing at a keybind-menu variable hundreds of lines
  from anything that changed. The new constants were regrouped into `JAW`,
  `SHAPES`, `CLAMP` and `RAMP` tables, which bought back a dozen slots.
  Anything substantial added here will hit it again; grouping into a table is
  the cheap fix, and a `do ... end` block around a section would free its
  locals entirely.

  *How it was checked.* The headless harness grew assertions for the ramp:
  no two-jaw column before `ramp_single_pipe_until`, none one-jaw after
  `ramp_two_pipe_by`, every pipe's opening matching the curve for the second
  it was built in, jaws always drawn where the hitbox says the edge is, and
  clamps only ever closing. Since a normal round is far too short to reach
  the later eras, it also runs against a staged copy with the ramp compressed
  into seconds. That compressed run found its own bug first: at a 1.5s single
  era, no pipe can exist yet at all -- the first one cannot appear before
  about 2s, since a coin has to be collected and then `COIN_PIPE_DELAY`
  passes -- so the thresholds had to clear that floor.

## 2026-09-27 — commit `TBD` ("Add teeth jaws, drifting columns and breathing clamps")

- **"continue design from last night"** -- picked up as *more pipe variety*.

  Three new kinds of pipe, each behind its own setting so any of them can be
  turned off from `gameSetting.csv`.

  *Teeth.* A fifth jaw shape: three small triangles tip to tip across the
  painted body. It is added to `SHAPE_DEPTH` in `tools/make_pipe_shapes.py`
  as the *last* entry on purpose -- speckle seeds are handed out by position
  in that dict, so adding it anywhere else would have repainted all 16
  existing jaws. Regenerating left those 16 byte-identical and added four
  files (10 KB). Each tooth reaches the same depth as a triangle's point, so
  it bites no deeper, but there are three tips to line up with, so it is
  trimmed to 0.85 of the notch. The profile is written on `u` rather than
  `|u|` so, with an odd number of teeth, the middle one's point lands on
  `u = 0` -- which is where `pipeAim` reads the tightest spot from.
  `shapeNotchPx` in main.lua mirrors it; checked against the generator at
  241 points (identical) and against the drawn edge of the art (within half
  a pixel).

  *Drifting columns.* The whole column -- jaws and opening together -- swings
  slowly up and down (35px either side, 3s a swing) as it comes. Any column
  can drift, one jaw or two, flat or shaped, except a clamp or a breather:
  an opening that is both moving and changing size asks two things at once.
  Each starts at a random point in its swing so a run of drifters is not a
  row moving in lockstep, and like a clamp it only advances while on screen.
  The amplitude is capped at `pipe_gap_half_height`, which is more than the
  closest any column is ever placed to the edge of where gaps can go, so a
  drifting jaw still covers the lane end to end -- the harness asserts that
  on every tick.

  Moving `p.y` meant the one-jaw aim point could no longer be worked out
  once at spawn and stored: `pipeAim` now derives it from the column's
  current edge, and coin placement calls `pipeAim` rather than reading the
  stored `aimY` fields, which are gone.

  *Breathing clamps.* A clamp that does not stay shut: flat jaws close to
  0.55 of the opening and reopen on a 1.6s rhythm, so the question is *when*
  to go through rather than whether there is room. Two-jaw columns only,
  rolled only for one the clamp roll passed over. It comes on screen wide
  open (the cosine starts at 1), so the first thing you see of one is its
  gap at its widest. Its tightest point is looser than a clamp's 0.45
  because it comes round again every breath instead of once.

  *Six more settings:* `breathe_pipe_chance` (0.12), `breathe_period`,
  `breathe_gap_min`, `drift_pipe_chance` (0.2), `drift_amplitude`,
  `drift_period`.

  *The AI needed telling again, twice.* With every column forced to drift,
  the AI crashed 30 times in 446 pipes against teeth. Its autopilot only
  pushes in proportion to how far off it is, so against a moving target it
  settles into trailing it -- about 18px behind at full drift speed, which on
  top of a 32px bob is more than a toothed opening leaves. `updateAI` now
  feeds forward how fast the aim point itself is moving, counted only while
  it is still the same pipe so that switching targets does not read as one
  enormous tick of motion. It keeps its 100ms reaction lag; it just no
  longer lags a *moving* target on top of that.

  Breathers killed it too, mostly late in a round when openings are already
  tight: the bob was sized off how open the gap was *this* tick, so when
  the jaws came back in the bird was still out near the edge. For a breather
  it is now sized off the tightest breath instead.

  *How it was checked.* The headless harness from earlier entries was not in
  the repo, so a fresh one was written: Solar2D stubs, main.lua run
  unmodified under Lua 5.1 through `lupa`, one exported table of internals
  appended before the game-loop timer. The player lane is flown
  "perfectly" -- held on `pipeAim` every tick -- so if it ever dies, an
  opening was not actually passable at its aim point; it never did. Each
  new pipe kind was run at 100% for 1000 simulated seconds with the AI's
  deliberate loss roll switched off and pipes fed into both lanes every
  1.5s, plus a mixed run with the ramp's tight era compressed to the start.
  Asserted every tick: clamps, breathers and drift never stack; breathers
  stay flat, two-jawed, inside their range, and open fully on their first
  frame; drift never passes its amplitude; jaws are drawn where the hitbox
  puts the edge and still reach both ends of the lane. After the two AI
  fixes, every scenario came in at 0-0.6 AI crashes per 100 pipes, in line
  with the existing clamp-only run (0.62) and baseline (0.21).

  *Not rebuilt.* Solar2D is not installed on this machine, so
  `build_output/` still holds the 2026-09-26 21:57 build, which predates
  both this entry and the last edits of the previous one.

## 2026-09-28 — commit `TBD` ("Phase the newer pipes in over a round")

- **"continue from my last design"** -- picked up as *tie the new pipes to
  the ramp*.

  Drift, teeth and breathers were rolled at full chance from the first
  column of a round. They now come in on the ramp's round clock, each with a
  window: never before `from`, then a chance climbing linearly from nothing
  to its full setting by `by`. Defaults put each one in an era: drift at
  10-30s, across the one-jaw opening where there is most room to fly round a
  moving pipe; teeth at 20-45s, as columns start pairing up; breathers at
  45-90s, once most columns have both jaws to breathe with. Clamps and the
  three older shapes are left as they were -- the request was about the
  new pipes.

  *Teeth are weighted, not gated.* A shape still being phased in counts for
  its unlock fraction in the shape roll, so half-unlocked teeth are half as
  likely as any other shape and a locked one simply drops out, rather than a
  failed teeth roll turning into a flat pipe. `pipe_shaped_chance` means the
  same thing it always did.

  *Kept out of the local count.* The windows and the lookup live on `RAMP`
  (`RAMP.unlocks`, `RAMP.unlocked`), not as new locals -- the 200-local
  ceiling from 2026-09-26 still stands.

  *Six more settings:* `ramp_drift_from`/`_by`, `ramp_teeth_from`/`_by`,
  `ramp_breathe_from`/`_by`. A `_by` at or below its `_from` switches that
  kind fully on at `_from`.

  *The same trade-off as the rest of the ramp.* A round ends on the first
  crash and typically runs ~16s, so at these defaults most rounds see a
  little drift and no teeth or breathers at all. That is what "held back"
  means on a per-round clock; lower the windows to meet them sooner.

  *How it was checked.* The harness now records the round time each pipe was
  built at and fails on any drift, teeth or breather built before its
  `from`. 3000 simulated seconds at the default settings (perfect player,
  AI's loss roll off so rounds run long enough to reach the later eras):
  none early. Shares in 10s buckets rise through each window and settle at
  about 14% drift, 11% teeth and 10% breathers -- what the chances predict
  once clamps take their cut. AI crash rate unchanged (3 in 1431 pipes). A
  backwards window (`from` 15, `by` 5) gave 0% before 15s and 100% after.

  *Still not rebuilt:* Solar2D is still not installed here.

## 2026-09-28 — commit `TBD` ("Build without Solar2D: repack the HTML5 package directly")

- **"forget about Solar2d, it's removed. Anyway, the single pipes (up/down),
  wider gaps, are not in the game"**

  *Why they were missing.* The build being played was never rebuilt after
  2026-09-19. Its file dates said 2026-09-26 21:57, but its package still
  carried the vk plugin removed on 09-24 and none of the jaw art, and every
  byte outside the compiled Lua and `gameSetting.csv` matches
  `ratcopter-web-current.zip`. So none of the one-jaw era, wider gaps,
  shapes, clamps or anything since had ever been in a playable build.

  *Building without Solar2D.* An HTML5 build is three parts: the wasm
  runtime and its loader zipped into `ratcopter.bin`, an Emscripten file
  package `ratcopter.data` (raw files back to back), and the index of that
  package, a JSON literal inside `ratcopter.js`. The game's Lua sits in
  `resource.car`, Corona's own archive, as compiled Lua 5.1 bytecode for a
  32-bit target. None of that needs Solar2D to change, only to be written in
  the same shape, so `tools/repack_html5.py` does exactly that:

  - compiles `main.lua` and `config.lua` with Lua 5.1 through `lupa` and
    rewrites the bytecode from the host's 64-bit layout to 32-bit. Only
    `size_t` differs (the length in front of every string), so the rewrite
    walks the chunk field by field and changes nothing else.
  - rebuilds `resource.car` with them (format worked out from the old one:
    a 16-byte header, a padded name index, 12-byte headed data blocks, and
    an 8-byte end marker that the first attempt missed).
  - swaps every non-Lua file in `mainGame/` into the package, adds new ones,
    rewrites the index, and gives the package a new UUID so a browser cannot
    serve a cached copy of the old one.

  `build.settings` is left as the last real build had it: CoronaBuilder
  consumed it at build time, and the current file has never been through a
  build. The vk plugin shims stay in `resource.car` for the same reason --
  they were there in every build that has run.

  *How it was checked.* The tool refuses to write anything unless its
  self-tests pass against the build it is about to replace: the old
  `resource.car` round-trips byte for byte, all four of CoronaBuilder's own
  bytecode chunks survive 32->64->32 unchanged, a fresh compile of
  `main.lua` survives 64->32->64 unchanged and still loads, and the `.bin`
  re-zips to identical members. Then the result was loaded in real Chrome
  through Playwright: it boots to the title screen, a click starts a round,
  and a one-jaw concrete column standing off the floor arrives in the
  player's lane -- the single-pipe era, live for the first time. The console
  shows the same audio-decode errors and 404s as the untouched 09-19 build
  under the same headless browser, and nothing else.

  *A slip, recorded.* The first repack ran in place on the assumption that
  `build_output/` was in git; it is gitignored. Nothing was lost -- the
  overwritten build is the 09-19 zip, byte for byte, as above -- but the
  README header now says where the base build lives.

- **"why is it just a black screen now"** / **"it's still a black screen"**

  *Browser cache, twice over.* The `.bin` carries the byte offsets of every
  file in the `.data`, so the two only load as a matched pair; a new `.bin`
  with an old `.data` is a black screen with no error. `python -m http.server`
  sends no `Cache-Control`, so Chrome is free to reuse either file for hours
  without asking. The server log showed exactly that: the page and the new
  `.bin` were fetched, and `ratcopter.data` never requested at all -- it came
  out of the cache from the old 09-19 build.

  Making it worse, nine stale `python -m http.server 8000` processes from
  09-17..09-27 were still running. Windows lets them share the port, and the
  ones bound to 127.0.0.1 won `localhost` over any server started since, so
  restarting "the" server changed nothing. All stopped.

  *Fixes.* `tools/serve.py` serves the build with `no-store`. That alone
  cannot evict a copy a browser already holds, so `repack_html5.py` now also
  stamps both download URLs with the build's id (`ratcopter.bin?v=...` in the
  pages, `ratcopter.data?v=...` in the loader): a URL no earlier build used
  cannot be answered from cache. Reproduced with a real Chrome profile
  poisoned by the 09-19 build served the old way: on reload the unstamped
  new build got the page from the server and both game files from cache;
  the stamped build fetched all three from the server and played.

## 2026-09-28 — commit `TBD` ("Turn triangle and half-moon tips into wide ground obstacles")

- **"for the triangle and curved pipes, the width of the pipe needs to be
  larger, they are not really pipes at that point, they are different type of
  shaped obstacles. so balance them based on that, give them another texture
  if needed. for example, Triangle can be a pyramid looking bricks, or a
  Trapezoid ramp, half-moon shapes can be an actual hump on the ground"**

  *Two ground obstacles replace two pipe tips.* The triangle becomes a
  stepped brick pyramid (3-6 courses of 28x18 bricks, each course half a brick
  in from each side, a single brick on top) and the half-moon becomes a hump
  (half an ellipse, 150x56 to 230x92). Both stand on the ground, 1.8-5x a
  pipe's width. Pipes keep the straight, pentagon and teeth tips.

  *Where they go.* A column's bottom half is a ground obstacle with
  `ground_obstacle_chance` (0.25), rolled after clamps and breathers so those
  keep their frequency. In the opening one-piece era an obstacle stands
  alone; once columns pair up, a flat pipe hangs above it -- flat, because a
  shaped tip biting down on an obstacle reaching up narrows one opening from
  both sides. There is nothing to choose about height: the obstacle's peak is
  fixed by its size, and the opening sits directly on it, with `p.y` still the
  centre of the opening, so `pipeAim` and coin placement needed no special
  case. Obstacles never drift -- the ground does not move.
  `pipe_shaped_chance` came down from 0.55 to 0.35 so pentagons and teeth
  still turn up about as often as when they were two shapes of four.

  *Width had to be taught to everything.* Each column now carries `halfW`,
  and spawning, spacing, clean-up and the AI's choice of target all measure
  off it rather than `PIPE_HALF_W`. Without that a wide obstacle would pop in
  already half on screen, vanish with half of it still showing, crowd the
  column before it, and the AI would start aiming for the next column while
  still over the back of a hump. Spacing is now between edges rather than
  centres, so two humps in a row keep a pipe-pair's clear run between them.

  *The hitbox is the outline.* `GROUND.surfaceAt` gives the obstacle's
  surface at any point across it; `tools/make_ground_obstacles.py` draws to
  that same outline. Checked column by column: the pyramids agree exactly;
  the humps within 1.6px except the outermost few pixels at their feet, where
  the ellipse is near vertical, drawn in 2px steps, and under 10px off the
  ground.

  *Balance.* A new bot flies the player lane with the real gravity and flap,
  a 125ms reaction lag and a noisy flap threshold, and anticipates its own
  fall the way a person does (without that it lagged into every bottom jaw).
  At the base opening it crashes at 11-14% of flat pipes -- and at 40% of
  the old triangle tips and 44% of the half-moons. The target was to leave
  the game as hard as it was, so each obstacle was matched to the tip it
  replaced. The knob is how much of the usual opening is left between the
  pipe above and the peak (`GROUND.open`): at 1.0 an obstacle column is no
  harder than a flat pipe (~12%), at 0.8 about 50%. Settled at 0.85 for the
  pyramid (42% on a fresh seed, target 40%) and 0.83 for the hump (45%,
  target 44%) -- a hump's broad crown leaves less room to sag across its
  width. Almost every crash is into the pipe above, not the obstacle: a
  steady flyer holds its height over the peak, so what decides difficulty is
  the room left, not the width.

  *Worth knowing:* the shaped tips were already three times as deadly as a
  flat pipe at the base opening -- pentagon 39%, teeth 45%, against 11-14%.
  Both jaws bite, so a triangle left 60px where a flat pipe leaves 100. The
  obstacles are matched to that level; if it feels harsh, raise
  `GROUND.open` towards 1.0.

  *Art.* Drawn at half size and doubled with nearest-neighbour to match the
  backgrounds' chunky pixels. Sewer: clay bricks, warmer than the green-grey
  wall so they read as something in the way, with moss and grime on the
  lower courses; a silt mound with a slime crust and stones (the first pass
  was too dark and disappeared into the wall). Surface: sandstone blocks; a
  grassy hill in the greens of the horizon bushes. 14 files, 23 KB. A theme
  switch re-skins obstacles already on screen.

  *Retired.* The eight triangle and half-moon jaw images are deleted and the
  pipe generator no longer draws them; the remaining 12 jaws came out
  byte-identical, since each shape's speckle seed is its position in
  `SHAPE_DEPTH` and those entries were kept. `repack_html5.py` now mirrors
  `Assets/` and `Sounds/` from `mainGame/` exactly, so art deleted there
  leaves the build too (it also dropped `Icon-1024.png`, gone from
  `mainGame/` since 09-24 and never loaded by the game).

  *How it was checked.* Rule harness, every tick: no obstacle on a clamp,
  breather or drifter; never with a bottom jaw or a shaped pipe above; opening
  sitting exactly on the peak; art standing on the ground; every column
  appearing wholly off screen, removed only once wholly off, and keeping a
  pipe-pair's clear run from the one before. Across default, everything-on
  and late-tight runs: no violations, no missing images, the perfect player
  never died, AI 0.3-0.44 crashes per 100 pipes, none on an obstacle. In
  Chrome, a build with every column an obstacle showed pyramids and humps
  riding in on both lanes; a theme switch re-skinned every obstacle in the
  harness (16 of 16).

## 2026-10-01 — commit `TBD` ("Floatier flaps and a THIS IS YOU tag")

- **"Make the bird have more airtime before it falls, so the game requires
  30% less input from players"**

  *The numbers.* One flap sets the bird's speed to `FLAP_VY` and gravity
  pulls it back, so it is back at the same height after `2*|FLAP_VY|/GRAVITY`
  seconds: 0.57s at the old 1500 / -430. Needing 30% fewer flaps means each
  one has to last 1/0.7 = 1.43x as long. Changing gravity alone would get
  there but make every hop 43% taller, which plays like a different game
  through the same gaps. Scaling the flap by 0.7 and gravity by 0.7^2 = 0.49
  gives the longer airtime and leaves the hop height (`FLAP_VY^2 /
  (2*GRAVITY)`) exactly where it was: `GRAVITY` 1500 -> 735, `FLAP_VY` -430
  -> -301. Airtime per flap is now 0.82s.

  *Side effects.* Falling and climbing are both slower, so getting from a
  low gap to a high one takes more lead. The AI lane never used gravity (its
  autopilot sets its speed directly), so it flies exactly as before. The
  09-28 obstacle balancing was measured with a bot flying the old physics,
  so those crash rates are no longer current.

- **"Add a "This is you!" Yellow floating text to my player screen that lasts
  3 seconds from the start"**

  *What it does.* When round 1 of a match starts, a yellow "THIS IS YOU!" in
  the game's font, with a black drop shadow, hovers just above the player's
  rat, follows it, bobs gently and fades out over the last half second of its
  3 seconds. Rounds 2-5 don't show it. It is hidden at once if the round ends
  early, and it ages on `gameLoop`'s ticks, so it pauses with the keybind menu.

  *Fitting it in.* It lives in the player lane's group, so it is clipped with
  the lane and never spills into the AI's side. It is clamped inside the lane
  (the rat starts near the left edge and can climb to the ceiling) and scaled
  down on a portrait phone, where the lane is narrower than the text. All its
  state sits in one `youTag` table, because `main()` is right at Lua 5.1's
  200-local limit: the first version, with its own locals, failed to compile.

  *How it was checked.* Rebuilt with `tools/repack_html5.py` on top of the
  09-19 zip (self-tests passed) and played in headless Chrome at 960x640 and
  390x844: the tag appears over the rat on the first tap, follows it, fits
  the lane in portrait and is gone on the elimination screen. The only
  console errors are the usual audio-decode ones.
