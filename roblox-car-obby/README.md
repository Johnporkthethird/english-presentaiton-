# Car obby: 100 object-world levels

## Showcase build: levels 1-10 (awaiting approval)

Levels 1-10 (the boot course, `Workspace.OBBY1`-`OBBY10`) are ten hand-designed themed levels. Each one is a journey
through its world rather than a flat line: spiral ramps up and down round a themed centrepiece, tunnels with boost
strips, caves (a craggy mountain you drive into, with a deadly floor and rocks to hop across), long ramps that climb and
dive, banked walled slides, narrow beams, big launches onto high ground and big drops, between the obstacle set pieces.
Heights change by 250-420 studs within a level and road widths run from 12 to 90 studs. `showcase-preview.jpg` shows one
piece from each.

| # | Level | Journey |
|---|-------|---------|
| 1 | Sugar Rush | Candy-cane spiral climb, candy-cane tube dive, gumdrop hops, candy-cane sweepers, cake-top launch, licorice tightrope, whipped-cream dive, frosted donut loop |
| 2 | Drive Thru | Drive-thru lane, ketchup ramp down, burger & fries hops, spatula catapult, straw bridge, milkshake spiral down, rolling pickle |
| 3 | Spore Springs | Hollow-trunk dive, glowroot cavern, vine climb, swinging leaves, mushroom bounce, toadstool tops |
| 4 | Checkmate | Castle gate, tower stair climb, rook leaps from the battlements, great board slide, pawn crushers, rotating chessboard, sceptre sweepers |
| 5 | Tick Tock | Clock tower climb, minute-hand walk, pendulum shaft drop, brass pendulums, gear tunnel, clock-hand sweepers, gear-tooth pistons |
| 6 | Toy Box | Race-track slide, track loop, spring launcher, alphabet block steps, playground slide, spinning tops |
| 7 | Orbit | Launch tube, zero-g planet hops, moonshot, station corridor, asteroid field, ring loop, satellite bridges |
| 8 | Eruption | Canyon descent, obsidian ledge, geyser blast, obsidian descent, lava geysers, crumbling crust |
| 9 | Frostbite | Bobsled run, ski jump, ice cavern, frozen lake, icicle crushers, glacier climb |
| 10 | High Score | Wormhole, pinball bumpers, plunger launch, coin climb, pixel tightrope, laser rhythm, neon loop |

- Every launch pad fires straight along its deck; roads may bend, pads never fire sideways (the validator checks it).
- Roads never get steeper than 19.5 degrees; spirals and slides have rails.
- `generator/polish.py` removes every pair of overlapping coplanar faces (the flicker), on all 100 levels.
- `generator/journey.py` has the journey pieces, `generator/journey_skins.py` how each theme draws them and each
  level's route, `generator/skins.py` the themes' objects and obstacles, `generator/showcase.py` the set pieces and level
  assembly. Levels 11-100 are still the earlier object-world versions below.

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
