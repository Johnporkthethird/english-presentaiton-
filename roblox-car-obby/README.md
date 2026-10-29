# Car obby: 100 object-world levels

## Testing the new levels

Open `good.rbxl` in Roblox Studio and press Play. The race course in Workspace (`OBBY1`-`OBBY10`) is levels 1-10, joined
to the start grid, the racing line (`RACING_START.CoursePath`) and the finish stadium. The world rotation normally swaps
in a random ten of the 100 levels after every race; in this file it is pinned to the main course (levels 1-10) by the
workspace attribute `ObbyDefaultCourse = "course1"`. Delete that attribute (or run
`python3 generator/test_course.py generator good.rbxl out.rbxl random`) to go back to random courses.

## Levels 1-10: the Mechanical Playground

Levels 1-10 form one long course in the sky, built from dark steel machinery. The roads are coloured, with hazard stripes,
glowing boost strips, gears and pistons. Each stage has its own accent colour. There is no background scenery: only the
track and its machines. The ten course slots run straight into each other:

| Stage | Name | What is in it |
|-------|------|---------------|
| 1 | Launch Runway | A wide runway with boost lanes and gantries, then a giant ramp through a suspended ring. You land on one of three routes: the central landing, a high narrow line (full speed only) or a low road that pads back up. Then an enclosed hammer corridor with crushers, swinging side hammers, overhead punches and sweeping arms, and its S-bend second hall. |
| 2 | Collapsing Highway | Tilting spans, a span that slides away and back, a falling tile span, and rolling spans on curves. A three-way split: the centre has spin gates and a turntable, the narrow right side is faster, and the lower left route has shaky tiles and a pad back up. |
| 3 | The Loop | A long acceleration ramp into a giant vertical loop. A bypass goes round it. A high shortcut fires you diagonally through the middle of the loop, with a recovery deck under it. Then the airborne sequence: a ramp up onto a sky deck, a long gap, and a split landing. The lower right deck leads by a precision hop to a hidden ledge that cuts the corner. |
| 4 | Crusher Works | An enclosed machine hall with crusher plates that slam together, lane walls that rise from the floor, floors that slide away, grinders on a reverse conveyor and a piston hall. An exit tunnel leads onto a launch ramp. Then a magnet crane carries the car over the void, and a fast belt runs under a row of presses. |
| 5 | Bridge Works | A swing span that turns half round, a sectional bridge of four quarter-turn sections, and a crossroads turntable. When the turntable stands at 90 degrees it lines up with a side spur, which is a safer way past everything. Also a see-saw bridge, a gear turntable, a pendulum ferry, a tilt gauntlet, and a lower route of small spinning platforms. |
| 6 | Demolition Yard | Wrecking balls of every size: across the road, down one lane, and huge slow ones on tall frames. A pair swings in opposite directions, then a wide escape ramp. A littered scrap heap, a drop, and a launch. Broken barriers and chains everywhere. |
| 7 | Corkscrew Tower | Piston lifts, then two banked laps spiralling down round a mechanical tower, with hops between the segments. The tower holds the road on spokes. Then a boost tunnel, a banked slalom and a second corkscrew. |
| 8 | Fan Tunnel | Giant fans with blades sweeping down through the road, each with its own size, speed and position. Shutters, a split duct with a small fan in each lane, close fans, an open-air jump, and updraft fans. |
| 9 | Smash Yard | Breakable crate and brick walls that you smash through at speed (they fly off and come back), and reinforced gates you must steer round. A cracked wall at the fork hides a straight shortcut. Wall gauntlet, reinforced maze, crate walls after the launch. |
| 10 | Final Gauntlet | A collapsing straight, a medley of every machine, a swing span and a see-saw, narrow jumps, crusher plates, and a boost run to the giant final ramp. A recovery deck under the ramp pads you back up. Victory lane and the finish arch. |

- Moving parts use the game's own systems:
  - `ObbyPropAnim` rigs for hammers, crushers, wrecking balls, fans, shutters and pistons.
  - The clock rotor engine for bridges that turn, rock and carry the car.
  - Sinking tiles for collapsing road.
  - The arcade brick walls (`ArcadeM = "bricks"`) for breakable walls.
  - `WallRide` for the loop.
  - The magnet ride for the crane.
  - Launch pads for lifts and updrafts.
- Two small changes outside the level geometry:
  - The `ObbyAssembler` position list now also moves `ClockRest` and `BrickFace` with a level, so rotors and brick walls work in any slot.
  - The level exporter marks brick walls as moving parts, so the validator does not count them as blocking the road.
- Code: `generator/mech.py` has the whole course; `generator/obby.py` has the links between platforms.
- The validator reports 0 issues on levels 1-10. **Not tested in Roblox Studio.**
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
