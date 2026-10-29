# Car obby: 100 object-world levels

## Testing the new levels

Open `good.rbxl` in Roblox Studio and press Play. The race course in Workspace (`OBBY1`-`OBBY10`) is levels 1-10, joined
to the start grid, the racing line (`RACING_START.CoursePath`) and the finish stadium. The world rotation normally swaps
in a random ten of the 100 levels after every race; in this file it is pinned to the main course (levels 1-10) by the
workspace attribute `ObbyDefaultCourse = "course1"`. Delete that attribute (or run
`python3 generator/test_course.py generator good.rbxl out.rbxl random`) to go back to random courses.

## Levels 1-10, version 3

`PLAN.md` has the plan and a review of each level. Each level is built round its own main idea, with no hoops and
no loops:

| # | Level | Main idea |
|---|-------|-----------|
| 1 | Sugar Rush | mega ramps off a giant cake (a ~600-stud jump over a chocolate river), a candy-cane slalom |
| 2 | Drive Thru | conveyor belts (turbo, sideways, backwards), grease, burger smashers |
| 3 | Spore Springs | chains of bounce mushrooms: steer in the air from cap to cap |
| 4 | Checkmate | knight jumps between towers, a chessboard that falls away under you, sliding rooks |
| 5 | Tick Tock | spinning gears, ticking clock-hand bridges and pendulums that carry the car |
| 6 | Toy Box | a slot-car race track: figure of eight over its own bridge, strips on every straight |
| 7 | Orbit | UFO tractor beams that carry the car across space, an asteroid belt at full speed |
| 8 | Eruption | down a volcano: crater spiral, lava tube, surging lava, a geyser blast out |
| 9 | Frostbite | a downhill ski run: switchbacks, ski jumps, black ice, rolling snowballs |
| 10 | High Score | laser gates on a beat timed to a boost deck's exact speed, pinball bumpers, ghosts |

- Speed: runs of boost strips take every car to 330 studs/s (the game's stack cap). Boost decks hold an exact
  speed where the next thing depends on it.
- Jumps are curved ramps sized for that speed. Each landing runway runs from the slowest take-off to past the
  fastest.
- Moving platforms use systems the game already has:
  - the clock rotor engine (gears, clock hands, pendulums);
  - sinking tiles (the chessboard);
  - magnet rides (the UFOs);
  - the junkyard's conveyors and oil.
- The ObbyAssembler now moves the clock rides' rest frames (`ClockRest`) with a level, like the checkpoints.
- Moving props pivot at their own centre, so the 1400-stud animation distance cull works.
- Scenery is measured after building, and anything touching a road or a flight path is moved.
- The validator flies every jump at its slowest and fastest take-off. Levels 1-10 report 0 issues.
- `generator/rush2.py` has the pieces and `generator/rush2_levels.py` the ten levels. `generator/epic.py` joins
  them to the start and finish.
- Levels 11-100 are still the earlier object-world versions below (they still have hoops and loops).

## How the levels are built

- 25 object worlds, each visited 4 times in a new colour set: mushrooms, chess pieces on checkerboards, dice on playing cards, spinning gears on I-beams, gumdrops and lollipops on chocolate bars, burgers on trays, sky islands with rope bridges, clouds on rainbow bridges, basalt crystal columns, planets you drive over, lily pads on bamboo rafts, drums on piano keys, toy bricks with studs, clock faces with turning hands, snowflakes on ice, golf greens on a running track, satellites with solar panels, circuit chips on boards, Greek columns, buoys and piers, sandstone mesas, obsidian with lava seams, arcade coins on pixel bricks, layered cakes on wafers, flowers on leaves.
- Every hop target and every surface you drive on is that world's object. Round or domed tops sit on an invisible flat floor so the car rides level. No background scenery.
- Each level also has its own layout grammar (straight, rising, falling, lane-switching, wave, steps), width scale and lane grid, so everything lines up.
- Most jumps are exact launch pads (`CarLaunchPad` + `LaunchExact`), so a hop lands in the same place at any car speed. Modules are joined by pad hops that change height, and each level ends on a pillar-hop finale.
- About 40 modules, quota-balanced so no piece is everywhere; the curvy stunt roads (wall ride, barrel roll, corkscrew, half-pipe, spiral) are capped at 3-7 levels each. Modules include: pillar bounce, cube climb / descent, big-air kicker through hoops, ring drop, windmill launch, loop-de-loop, double loop, barrel roll, wall ride, glass pipe (with a spinning bar), corkscrew, spiral, half-pipe, rotating cross, spinning bridges, sweeper discs, holey turntable, swinging platforms, sliding bridges, piston wave, crushers, laser rhythm gates, laser limbo beam, moving doors, crumbling checkerboard, tilt runs, zigzag beams.
- New in this version: rotating doors with a gap, spinning log bridges, spiral hop towers, long jumps through hoops, drop shafts, split lanes, conveyor belts, an ice rink with holes, bumper fields. No two levels share a sequence.
- Loops, rolls, wall rides, pipes and the corkscrew carry `WallRide`, which is what lets the car controller hold a car on steep and upside-down surfaces.

Every level keeps its original `Length` and starts and ends on the course centre line at road height, so the WorldRotation / ObbyAssembler shuffle and the stadium placement work as before.

## Rebuilding

Plain Python 3 (`pip install lz4 zstandard numpy`):

```bash
python3 generator/cache.py generator place.rbxl place.pkl
```

```bash
EXPORT_DIR=preview python3 generator/build.py generator place.pkl out.rbxl && python3 generator/validate.py preview
```

`worlds.py` holds the 25 object worlds, `levels3.py` the recipes, `parkour3.py` (with `parkour.py`) the modules, `validate.py` the geometry checks (road under the racing line, every pad flight lands, nothing solid on the line, safe checkpoints, kill floors, slopes).
