# Car obby: 100 object-world levels

## Showcase build: levels 1-10 (awaiting approval)

Levels 1-10 (the boot course, `Workspace.OBBY1`-`OBBY10`) are ten big themed journeys. A level is no longer a line down
the course: the route winds across a 5,400 by 2,500 stud area, turns back on itself, spirals up and round giant
landmarks, crosses over its own track, and climbs and dives by 300-450 studs. Each level is 9,000-16,000 studs of
driving with its own shape and its own centrepiece. Road widths run from 12-stud tightropes to 260-stud arenas.
`showcase-preview.jpg` shows every level from above and up close.

| # | Level | Shape | Journey |
|---|-------|-------|---------|
| 1 | Sugar Rush | Spiral up a mountain | Sprinkle stampede; spiral up a giant three-tier cake past cake-knife sweepers; macaron towers; candle-flame crown; cherry leap off the top; candy-cane slide; licorice tightrope; gingerbread launch; wafer floor; lollipop spiral; donut loop; gumdrop bumpers |
| 2 | Drive Thru | Zig-zag legs | Drive-thru lane; conveyor grill; patty smashers; fry-forest hops; plate spinners; 1.5 laps up a giant burger; spatula catapult; milkshake spiral down; straw tightrope; salt and pepper rush; rolling pin |
| 3 | Spore Springs | Up a giant tree | Hollow trunk; glowroot cavern; shelf-fungus spiral up the Great Tree past swinging leaves; canopy cap hops round the crown; vine tightrope; rolling log; leaf slide; spore bumpers; puffball field |
| 4 | Checkmate | Board, then castle | Pawn stampede; knight's-tour L-hops across a giant chessboard; grand board rotors; switchbacks up the castle wall; battlements; drawbridge leap; tower stair down |
| 5 | Tick Tock | Round a clock face | Gear steps; escapement pistons; a lap of a giant clock's rim with the minute hand sweeping across it; cuckoo leap; pendulum hall; mainspring spiral; cog bridges; gear teeth; balance wheel |
| 6 | Toy Box | Track that crosses itself | Big banked loop over the start straight; crossover bridge; track loop; wall ride; block tower; spring launcher; domino crushers; playground slide; toy-train crossing; toy bumpers |
| 7 | Orbit | Planet to planet | Launch tube; a ring road round Mars; slingshot; ring-shard hops round a ringed planet; comet dive; station spin; zero-g tube; ring loop |
| 8 | Eruption | Down a canyon and out | Switchbacks down into a lava canyon; lava river road; obsidian stones; magma chamber; crumbling crust; geyser blast; lava pistons; lava fall |
| 9 | Frostbite | Summit, then hairpins | Spiral up an ice spire; ski jump; four hairpins down the mountain past crushers, swings and sweepers; ice cavern; frozen lake; avalanche; icicle crushers |
| 10 | High Score | Neon maze | Coin slot; a right-angle neon maze with sliding doors; pinball table; plunger launch; tetris-stack hops; neon loop; joystick spiral; laser grid |

- `generator/route.py` lays a route in any direction: straights, banked turns, spirals round a centre, rollers, smooth
  connectors, pad jumps and hop chains. Any older set piece (built along +X) is built in place and turned to the
  route's heading, with its pads, checkpoints and racing line.
- Every launch pad still fires straight at its landing; the validator checks each pad's direction against its jump.
- `generator/epic_levels.py` has the ten routes, `generator/epic_marks.py` the giant landmarks,
  `generator/epic_kit.py` the new set pieces (rotor arenas, sliding-block lanes, piston seas, crumble floors, bumper
  fields, turntables, wide conveyors) and obstacles that sit on any road, `generator/epic.py` the level assembly.
- Every level stays inside its own X box (the next level starts there) and starts and ends on the course centre line, so
  the shuffle and the stadium still line up. Fall triggers sit on a grid under the lowest road nearby.
- `generator/polish.py` removes every pair of overlapping coplanar faces (the flicker). Levels 11-100 are still the
  earlier object-world versions below.

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
