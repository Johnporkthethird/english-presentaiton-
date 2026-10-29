# Levels 1-10, version 3: plan and review

## What was wrong with version 2

- Every level was the same recipe in different colours: ramp jump, sweepers, stepping stones, drop steps, ramp jump.
- Slow: no speed strips, so the car only ever drove at its own top speed, and every jump was about 250 studs.
- Easy: wide decks, landings 150-380 studs long, nothing that needed real steering or timing.
- Spammy: windmills and sweepers in every level.
- Hoops round every jump and loops in four levels (gone).

## Rules for every level

- No hoops, no loops, no tubes.
- Speed from the game's own boost rules (TorretaControlsClient):
  - **Boost strips** (`BoostStack`) stack up to the cap of 330 studs/s, so after a strip run every car leaves the
    lip at about 330 whatever its build. Every big ramp is sized for that speed.
  - **Boost decks** (a road whose parts carry `BoostSpeed`, no stacking) hold every car at an exact speed. They are
    used where the next thing depends on your speed: bounce chains (260), knight jumps (200), laser beats (260).
- Ramps are real curved ramps. The car flies along the last slope of the ramp and gravity is real, so every flight
  can be worked out. Each landing runway starts short enough for a car at 90% of the speed and runs on past the
  fastest one. Space held on a lip at full speed throws a car much further. That case is checked too, but the driver
  is expected to brake in the air for it (S works in the air).
- One main idea per level, and no other level uses it as its main idea. At most three kinds of obstacle per level.
- Corners taken at full boost speed have a radius of at least 340: the car can only turn so fast at speed.
- A checkpoint before every hard part.
- Moving platforms use the game's own systems, which already carry a car on a moving deck:
  - gears, clock hands and pendulums use the clock level's rotor engine (ClockKinematicClient);
  - the falling board uses its sinking tiles (ClockSand);
  - UFOs use the magnet rides (ObbyMechClient);
  - belts and grease use the junkyard's conveyors and oil.

## The ten levels

| # | Level | Main idea | Shape | Height |
|---|-------|-----------|-------|--------|
| 1 | Sugar Rush | **Mega ramp.** A strip run off the top of a giant cake into a ~600-stud jump over a chocolate river, a candy-cane slalom, a second ramp onto a narrow wafer runway | spiral round the cake, then one long line | up 250, then a long plunge |
| 2 | Drive Thru | **Conveyor kitchen.** A turbo belt off the counter, grease before a corner, sideways belts over the sink, a backwards belt under burger smashers, fry-basket drops, express belts | right-angle zigzag | flat with counter drops |
| 3 | Spore Springs | **Bounce chain.** Giant mushroom caps throw you up as you land; steer in the air onto the next one (left, right, higher, lower); three chains with a root slide between | wide weave | mostly in the air |
| 4 | Checkmate | **Falling board.** Knight jumps between towers (an L: turn in the air onto the next), a board whose squares drop just after you pass, rooks sliding across it, a sprint over a board collapsing behind you | square round a giant chessboard | towers up, then down |
| 5 | Tick Tock | **The clock's works carry you.** Spinning gears, clock-hand bridges that tick round (cross while they line up), pendulums that ferry you over the drop, then up round the clock tower and off the top | line, then a spiral climb | climbs |
| 6 | Toy Box | **Slot-car speedway.** A narrow railed track with strips on every straight: a figure of eight over its own bridge, a hairpin, a chicane, three track-gap jumps, toy crushers | figure of eight | flat, plus the bridge |
| 7 | Orbit | **Tractor beams.** UFOs grab the car and carry it across empty space; a launch-pad leap with long hang time; an asteroid belt threaded at full speed; a ring road round a ringed planet | open arcs | high up |
| 8 | Eruption | **Down the volcano.** A spiral down inside the crater, a lava tube with a roof and lava jets, causeways that lava surges over, a geyser that blasts you out, an ash slide | spiral, then tunnel | deep down, then up |
| 9 | Frostbite | **Downhill ski run.** The chairlift throws you to the summit; a black run, switchbacks, black ice, two ski jumps, rolling snowballs, a frozen lake, ski cross | switchbacks | downhill all the way |
| 10 | High Score | **Arcade rhythm.** Boost decks hold you at exactly 260 while laser gates flash on a beat timed to that speed: hit the first gap and you clear the row. Pinball bumpers, ghosts across the lanes, a high-score jump | square wave | flat, the hardest |

## Review of each level

| # | Fast | Fun moment | Hard but possible | Glitch risk and what was done | Unique |
|---|------|------------|-------------------|-------------------------------|--------|
| 1 | 330 on both ramps | the river jump | wide first runway; the second is 48 wide (steer in the air) | a crest at 330 would throw the car, so the roll-in is gentle and straight | only level built round huge ramps |
| 2 | belts add up to +140 | being flung off the counter | sideways belts with no rail on the push side; grease into a corner | belts use the game's conveyor code, eased in and out | only level with belts and grease |
| 3 | 260 held all the way | chained bounces | each cap is 110-120 wide; flights checked from 234 to 260 | caps are the game's bounce mushrooms (the whole cap fires) | only bounce level |
| 4 | 200 on the decks | turning mid-air onto a tower | sinking squares need you to keep moving | tiles use the game's sinking-sand code, which refills | only level where the floor falls |
| 5 | 330 strips between rides | riding a pendulum over the drop | timing the hands and pendulums | carried by the game's rotor engine (it also turns your heading with a gear) | only level that carries you |
| 6 | strips on every straight | flat out over your own bridge | narrow track, crushers | every bend is wide enough to take at speed | only race-track level |
| 7 | 330 launches | being picked up by a UFO | threading the asteroid gaps at 330 | the beam uses the game's magnet ride (the same lift and drop) | only level with tractor beams |
| 8 | strips on the rim and slide | the geyser blast | lava surges on a timer | lava rises and falls on server time, so everyone sees the same surge | only underground level |
| 9 | gravity plus strips | the ski jumps | black ice before jumps, snowballs | landing hills are long and downhill | only downhill level |
| 10 | held at exactly 260 | clearing a whole row of lasers on the beat | the hardest: three rows of beat gates, ghosts, bumpers | gates flicker before they switch on | only rhythm level |

## How it is checked (`generator/validate.py`)

- Every jump is flown at the slowest and fastest speed it can take off at, and must come down on its runway or cap.
- There must be road under the racing line, and nothing solid in the way of the car along it.
- No scenery may sit where the car drives or flies.
- No bumps in the road.
- Checkpoints must stand on road and away from hazards.
- Scenery is placed by measuring each landmark after building it: anything that would touch a road or a flight path
  is taken down and put somewhere else.
- Moving decks, magnet rides and sinking tiles are checked for a deck under the line (they are flagged as moving).
- Not tested in Roblox Studio from here: the moving decks, beams and boosts rely on the game's existing scripts, which
  were read but not run.
