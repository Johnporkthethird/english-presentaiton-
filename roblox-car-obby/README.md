# Car obby: 100 object-world levels

## Showcase build: levels 1-10 (awaiting approval)

Levels 1-10 (the boot course, `Workspace.OBBY1`-`OBBY10`) are now ten hand-designed themed levels, each with 6-7 set pieces drawn in its theme, Roblox's textured materials instead of flat plastic, and themed structures under every deck. `showcase-preview.jpg` shows one set piece from each.

| # | Level | Theme | Set pieces |
|---|-------|-------|------------|
| 1 | Sugar Rush | Candy land | Gumdrop climb, candy-cane sweepers on cookies, lollipop turntable, frosted donut loop, licorice conveyors, chocolate crumble |
| 2 | Drive Thru | 50s diner | Burger & fries hops, ketchup & mustard gates, milkshake tower, rolling pickle, swinging spatulas, burger presses |
| 3 | Spore Springs | Glowing mushroom forest | Toadstool hops, giant mushroom climb, hollow log, swinging leaves, spore-ring drop, puffball field |
| 4 | Checkmate | Chess board | Rook hops, sliding castle walls, pawn crushers, rotating chessboard, sceptre sweepers, knight leaps |
| 5 | Tick Tock | Clockwork | Gear climb, clock-hand sweepers, brass pendulums, clock tower, gear-tooth pistons, cog bridges |
| 6 | Toy Box | Toy box | Alphabet block steps, spinning tops, domino path, toy swings, hula-hoop leap, sliding brick walls |
| 7 | Orbit | Outer space | Planet hops, satellite bridges, asteroid field, ring loop, moonshot, meteor drop |
| 8 | Eruption | Volcano | Obsidian descent, lava geysers, crumbling crust, flame sweepers, magma pistons, caldera drop (over a lava sea) |
| 9 | Frostbite | Ice and snow | Snowflake hops, ice rink, icicle crushers, glacier wall ride, snowflake bridges, snowman slalom |
| 10 | High Score | Neon arcade | Coin wave, pinball bumpers, laser rhythm, pixel path, neon loop, equaliser bars, invader walls |

Polish pass:
- Every launch pad in levels 1-10 fires straight down the course. There are no sideways lane-change hops; the tower climbs go straight up beside their tower, and the loop exit steers back into lane on a wide deck. The validator checks this.
- No flickering surfaces. `generator/polish.py` finds every pair of visible faces that share a plane and overlap (z-fighting), and pushes the decoration (or the smaller face) 0.15 studs clear. Levels 1-10 had 80-1,500 of these each and now have none. The pass runs on all 100 levels.

`generator/skins.py` holds the ten themes (every hop target, deck, pad, hoop and moving hazard is drawn by the theme); `generator/showcase.py` holds the set pieces and the level order. Levels 11-100 are still the earlier object-world versions below.


`good-redesigned.rbxl` is the uploaded place with all 100 levels in `ServerStorage.OBBY_POOL` (L001-L100) rebuilt as clean parkour courses. The boot course in `Workspace` (OBBY1-OBBY10) and `RACING_START.CoursePath` are rebuilt from the new levels 1-10. Scripts, lobby, garage, stadium and UI are unchanged.

`levels.json` lists every level's title, style and modules in order.

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
