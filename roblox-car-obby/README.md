# Car obby: 100 object-world levels

## Testing the new levels

Open `good.rbxl` in Roblox Studio and press Play. The race course in Workspace (`OBBY1`-`OBBY10`) is levels 1-10, joined
to the start grid, the racing line (`RACING_START.CoursePath`) and the finish stadium. The world rotation normally swaps
in a random ten of the 100 levels after every race; in this file it is pinned to the main course (levels 1-10) by the
workspace attribute `ObbyDefaultCourse = "course1"`. Delete that attribute (or run
`python3 generator/test_course.py generator good.rbxl out.rbxl random`) to go back to random courses.

## Showcase build: levels 1-10 (awaiting approval)

Levels 1-10 (the boot course, `Workspace.OBBY1`-`OBBY10`) are non-stop jump levels: no long roads. Every level is a run
of short beats (a ramp jump through rings onto a downhill landing ramp, a drop cascade, a bounce up onto a mushroom or a
cake, quick island hops, a short gauntlet of sweepers, crushers or lasers, a windmill whose blades sweep through the
flight, loops, wall rides, tubes). Each level has its own shape, length, height profile and look.
`showcase-preview.jpg` shows three driver's-eye moments from each.

| # | Level | Idea |
|---|-------|------|
| 1 | Sugar Rush | Sugar Avalanche: fired onto a giant cake, then a candy downhill of jumps, drops and gumdrop hops (an S) |
| 2 | Drive Thru | Kitchen Chaos: flat out in right angles: belts, smashers, burger hops, a bun bounce, frying-pan drops |
| 3 | Spore Springs | Bounce Forest: up and down all the way: mushroom bounces, cap dives, toadstool hops (an organic weave) |
| 4 | Checkmate | Knight Moves: L-shaped knight hops between towers over a giant board, rook sliders, a crumbling board |
| 5 | Tick Tock | Clock Tower Drop: launched up, then jumping down round a clock tower in a square spiral |
| 6 | Toy Box | Stunt Track: kickers through rings, two loops, two wall rides, a tube, banked hairpins |
| 7 | Orbit | Moon Jumps: a few huge floaty leaps between planets through long rows of rings |
| 8 | Eruption | Meltdown: drop after drop into a lava canyon, then a geyser blasts you out |
| 9 | Frostbite | Avalanche Run: shot to the summit, then ski jumps straight down the mountain |
| 10 | High Score | Rhythm Rush: rapid-fire short hops on a narrow neon track in a square wave, laser gates between |

- `generator/rush.py` has the beats, `generator/rush_levels.py` the ten levels, `generator/route.py` lays them in any
  direction, `generator/epic_marks.py` the giant landmarks, `generator/epic_kit.py` the arenas and obstacles.
- Jumps the car can clear on its own are real ramps: a solid kicker wedge you drive off with the car's own jump, and a
  long landing deck so any normal speed lands.
- Boosters (`LaunchPad`, `BoosterUp`) only push straight up: they keep your speed and direction and set the upward
  speed, and you steer in the air to land where you want. None fires you in a set direction (`LaunchForward` is gone).
  They are only used where a climb is too high for a normal jump.
- Moving props animate: each animated model's pivot sits at its own centre, so `ObbyPropAnim`'s 1400-stud distance
  cull no longer hides them (before, every pivot was at the level origin).
- No phasing: scenery the car can reach (big blocks, wedges, round shapes) is solid; checkpoint flags stand at the road
  edge; cakes, mushrooms and asteroids sit beside the landings instead of through them; rook sliders have a solid block
  with a hazard; loops are bigger (radius 64), thicker and smoother, with nothing in the entry and exit lanes. The
  validator checks the flight path and racing line against every solid part.
- Every level stays inside its own X box and starts and ends on the course centre line, so the shuffle still works.
- Models: a seated teddy bear, a rubber duck, a spinning top, lettered alphabet blocks, giant toadstools, a horse-headed
  knight, a four-faced clock tower, low-poly snowy peaks and pine trees (smooth faceted cones built from wedge
  triangles), an arcade cabinet with a lit screen, joystick and buttons. `models-preview.jpg` shows them;
  `generator/gallery.py` (`GALLERY=1`) builds them all in a row for inspection.
- No flicker: `generator/polish.py` resolves overlapping flat faces and now also round ones (stacked same-size
  cylinders, coincident balls). Every level of the 100 ends with 0 fights.
- No bumps: road bends are mitred (slabs meet edge to edge, a flush triangle closes the outside of each bend) instead of
  overlapping, turns are flat (the toy-track hairpins ease their bank in gradually), crumbling floors have hairline
  seams, and the validator samples the road height under both wheels every 2 studs along the line and flags any step.
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
