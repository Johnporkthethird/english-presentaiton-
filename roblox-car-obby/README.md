# Car obby: 100 object-world levels

## Testing the new levels

Open `good.rbxl` in Roblox Studio and press Play. The race course in Workspace (`OBBY1`-`OBBY10`) is levels 1-10, joined
to the start grid, the racing line (`RACING_START.CoursePath`) and the finish stadium. The world rotation normally swaps
in a random ten of the 100 levels after every race; in this file it is pinned to the main course (levels 1-10) by the
workspace attribute `ObbyDefaultCourse = "course1"`. Delete that attribute (or run
`python3 generator/test_course.py generator good.rbxl out.rbxl random`) to go back to random courses.

## Levels 1-10, version 5: set-piece tours

Each level is a tour through set pieces, and what you land on is the object itself:

| # | Level | Set pieces |
|---|-------|------------|
| 1 | Stunt Show | drop into a laser box, a ramp through a ring of fire, star jumps, the hexagon mega ramp, a rocky downhill |
| 2 | Island Hop | islands in the sea, bobbing boats, a ring of fire, a lighthouse, a ferry |
| 3 | Rooftop Run | city rooftops at every height, a laser box, a skyscraper ramp |
| 4 | Sky Garden | clouds, bounce mushrooms, stars, a ring of fire |
| 5 | Clockwork Town | town rooftops, spinning gears, a clock-hand bridge, a pendulum ferry, music-box keys that sink |
| 6 | Pipe Dream | warp pipes, sinking piano keys, a ring of fire, a power star, a laser box |
| 7 | Orbit | stars in space, UFO tractor beams, a space-station laser box, a comet ramp, the moon surface |
| 8 | Eruption | an ash slope, rings of fire, islands in a lava lake, a lava causeway, a geyser |
| 9 | Frostbite | a black run, a ski jump, ice floes, an ice breaker, an avalanche run |
| 10 | High Score | laser mazes, neon piano keys, a bonus star, warp pipes, a boss box |

- How it works:
  - Every top you drive on is an invisible boost floor inside the object. It holds every car at the level's speed,
    so each jump is the same for every car.
  - Drops, kickers and up pads join the pieces. Each landing is checked from 80% to 100% of that speed.
  - Seas and lava kill on contact.
- Code: `generator/stages.py` has the set pieces and `generator/rush4_levels.py` the ten tours. `generator/obby.py`
  has the links and traps.
- The validator reports 0 issues on levels 1-10. Not tested in Roblox Studio.
- Levels 11-100 are still the earlier object-world versions below.

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
