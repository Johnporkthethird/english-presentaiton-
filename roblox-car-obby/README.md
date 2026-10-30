# Car obby: 100 object-world levels, two built courses

## Testing the new levels

Open `good.rbxl` in Roblox Studio and press Play.
- **Obby 1** (the Mechanical Playground, levels 1-10) is packed in Workspace (`OBBY1`-`OBBY10`), so the first race
  plays it. The course is joined to the start grid, the racing line (`RACING_START.CoursePath`) and the finish stadium.
- **Obby 2** (the Extreme Speedway, levels 11-20, the game's `course2`) comes in at the next intermission.
- After that the two take turns, one race each.

How the turns work:
- The workspace attribute `ObbyDefaultCourse = "course2,course1"` sets the pin. The WorldRotation script reads it, and
  a list of keys takes turns.
- To play only one obby, set the pin to `course1` or `course2`.
- To go back to the normal random ten of the 100 levels, delete the attribute, or run
  `python3 generator/test_course.py generator good.rbxl out.rbxl random`.
- The dev course picker can also load `course2` directly.

## Levels 1-10: the Mechanical Playground

Levels 1-10 form one long course in the sky, built from dark steel machinery. The roads are coloured, with hazard stripes,
glowing boost strips, gears and pistons. Each stage has its own accent colour. There is no background scenery: only the
track and its machines. The ten course slots run straight into each other:

| Stage | Name | What is in it |
|-------|------|---------------|
| 1 | Launch Runway | A wide runway with boost lanes and gantries, then a giant ramp through a suspended ring. You land on one of three routes: the central landing, a high narrow line (full speed only) or a low road that pads back up. Then an enclosed hammer corridor with swinging side hammers, side pushers and sweeping arms, and its S-bend second hall. |
| 2 | Collapsing Highway | Tilting spans, a span that slides away and back, a falling tile span, and rolling spans on curves. A three-way split: the centre has spin gates and a turntable, the narrow right side is faster, and the lower left route has shaky tiles and a pad back up. |
| 3 | The Loop | A long acceleration ramp into a giant vertical loop. A bypass goes round it. A high shortcut fires you diagonally through the middle of the loop, with a recovery deck under it. Then the airborne sequence: a ramp up onto a sky deck, a long gap, and a split landing. The lower right deck leads by a precision hop to a hidden ledge that cuts the corner. |
| 4 | Crusher Works | An enclosed machine hall with crusher plates that slam together, lane walls that rise from the floor, floors that slide away, grinders on a reverse conveyor and a hall of side pushers and hammers. An exit tunnel leads onto a launch ramp. Then a magnet crane carries the car over the void, and a fast belt runs past swinging hammers and sweeping arms. |
| 5 | Bridge Works | A swing span that turns half round, a sectional bridge of four quarter-turn sections, and a crossroads turntable. When the turntable stands at 90 degrees it lines up with a side spur, which is a safer way past everything. Also a see-saw bridge, a gear turntable, a pendulum ferry, a tilt gauntlet, and a lower route of small spinning platforms. |
| 6 | Demolition Yard | Wrecking balls of every size: across the road, down one lane, and huge slow ones on tall frames. A pair swings in opposite directions, then a wide escape ramp. A littered scrap heap, a drop, and a launch. Broken barriers and chains everywhere. |
| 7 | Corkscrew Tower | Piston lifts, then two banked laps spiralling down round a mechanical tower, with hops between the segments. The tower holds the road on spokes. Then a boost tunnel, a banked slalom and a second corkscrew. |
| 8 | Fan Tunnel | Giant fans with blades sweeping down through the road, each with its own size, speed and position. Shutters, a split duct with a small fan in each lane, close fans, an open-air jump, and updraft fans. |
| 9 | Smash Yard | Breakable crate and brick walls that you smash through at speed (they fly off and come back), and reinforced gates you must steer round. A cracked wall at the fork hides a straight shortcut. Wall gauntlet, reinforced maze, crate walls after the launch. |
| 10 | Final Gauntlet | A collapsing straight, a medley of hammers, sweeping arms and pushers, a swing span and a see-saw, narrow jumps, crusher plates, and a boost run to the giant final ramp. A recovery deck under the ramp pads you back up. Victory lane and the finish arch. |

- Moving parts use the game's own systems:
  - `ObbyPropAnim` rigs for hammers, crusher plates, pushers, wrecking balls, fans, shutters and pistons.
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
- The validator reports 0 issues on levels 1-10, and the clipping audit is clean (see below). **Not tested in
  Roblox Studio.**
- Levels 21-100 are still the earlier object-world versions below.

## Levels 11-20: Obby 2, the Extreme Speedway

A second, completely different course: a futuristic stunt playground high in the sky. Roads are dark metal with
neon edges and boost strips built into them, and giant rings hang over the jump lines. There is no background
scenery, only the course.

Each stage has its own colours:

| Stage | Colours |
|-------|---------|
| Boost Blast | graphite and fire orange |
| Splitter | navy and electric blue |
| Pinball Run | a purple table with magenta and cyan |
| Skyline Leap | steel blue and cyan |
| Rolling Thunder | violet |
| Cracking Canyon | rust and lava |
| Mega Ramp Cascade | lime |
| Laser Slalom | black and laser red |
| Speed Frenzy | gold |
| Grand Finale | white |

It is all speed: huge ramps, chained jumps, risky shortcuts and near misses. There are no presses, slow lifts or doors
to wait for.

| Stage | Level | What is in it |
|-------|-------|---------------|
| 1 | Boost Blast | A wide dive onto boost strips, then a massive jump through a giant ring onto a long runway. A steep side ramp on the left flies to a sky shortcut. Then a boost carve, a canyon gap, three launch pads up, a sky dive and the rocket ramp. |
| 2 | Splitter | A three-way split under green, yellow and red arches. The safe route is wide and easy. The middle route is a chain of six quick hops. The risky route has narrow beams and big gaps, and comes down past the merge. Then a crossover where the high road passes over the low one, a lane dash and a commit jump. |
| 3 | Pinball Run | A plunger launch, then a playfield of padded pop bumpers with slingshot banks. Spinning stars and flippers to squeeze past, angled ramp shots between raised platforms, a bumper bend, the jackpot ring and the drain. |
| 4 | Skyline Leap | A slalom round giant towers, then two launch pads up to the skyline deck. A steep ramp flies across the whole canyon through several rings. The narrow "Needle Gap" kicker threads between two towers. Then a banked bend and rooftop hops. |
| 5 | Rolling Thunder | Barrel gates (giant rings round the road, each rolled further), banked sweepers with the racing line painted on, and the Thunder Bowl: once round a giant spinning ring, climbing over your own way in. Then high platforms linked by hops, a roll ramp and a downhill burst. |
| 6 | Cracking Canyon | Road that cracks and drops away just after you drive on it, tilting spans and mesa hops. A long bridge breaks apart right behind you, or you can take a ledge route below it. A crumbling launch over the canyon and a last crack-up. |
| 7 | Mega Ramp Cascade | Land, accelerate, launch again: a chain of ever bigger jumps with strips on every landing. An expert line takes a steeper ramp onto a high rail. Then a curved road, two launch pads, and the Mega Launch. |
| 8 | Laser Slalom | Fixed laser fences with wide openings (and narrow coin slots), low laser hurdles to jump, sweeping beams that cover half the road, pulse gates where one half is always open, laser rotors, and the prism jump. |
| 9 | Speed Frenzy | A boost runway, two left-right chicanes with bollards, gaps that get bigger and bigger, and a medley of bumpers, laser fences and cracking road. |
| 10 | Grand Finale | A reprise of the best bits, a collapsing bridge, a launch pad, pulse gates, and the final jump through a giant double ring. You land on a huge bright finish platform and drive under the finish ring with its fireworks. |

- **Rewards:**
  - Coin clusters sit along the risky lines, inside the hard rings and on the shortcut flights. They use the game's
    own coins.
  - The coin layer now also puts a coin on every `CoinSpot` part a level places. That is a few lines added to
    `TorretaControlsServer`; no new currency or system.
- **Moving parts use the game's own systems:**
  - `ObbyPropAnim` rigs for spinners, flippers, sweeping beams and rotors.
  - The clock rotor engine for tilting spans.
  - Sinking tiles for cracking road.
  - Launch pads.
  - `ObbyHazard` Knock for bumpers and Zap for lasers. Pulse gates use the hazard's own timing, so the laser kills
    only while it is lit.
- **Code:** `generator/speedway.py`. Checkpoints use the game's `CarObbyCheckpoint` system.
- The validator reports 0 issues on levels 11-20 (and 1-10). It flies every jump and alternate-route jump at the
  slowest and fastest take-off speeds. **Not tested in Roblox Studio.**

## Clipping audit and tidy pass (all levels)

`generator/audit.py` checks a built place for parts that clip into each other:
- **Moving parts:** every moving machine (prop rigs, nested, and the clock-rotor bridges) is swept through its whole
  motion using the game's own maths. It reports anything that comes to pass through a solid part.
- **Through the road:** decorations that stick up through a road surface.
- **Ghosts:** visible parts of a dangerous machine that a car would drive straight through.

Levels 1-20 audit clean. The one leftover is a thin floor decal on a sloped road.

The older levels (21-100) had machines sweeping into their neighbours. These are fixed at the source:
- **Turntables:** sectors now end inside the disc. Their corners used to cut a few studs into the decks on either side.
- **Rotating doors:** the hub is higher and the blades shorter, so they no longer turn through the deck.
- **Hub posts:** the posts under turntables and spinning crosses are smaller, so the moving parts clear them.
- **Gear platforms:** the teeth are inlaid in the rim.
- **Snowflake platforms:** the arms end at the platform's edge.

Every build also runs a tidy pass on every level, 1 to 100:
- **Clear the line:** decorations across the racing line are removed (the validator's own drive-through test). This
  fixed the trees, castle merlons, clouds, gems and lamps in the car's way in the older levels.
- **Every bit hurts:** every visible piece of a moving machine (hammer arms, hubs, chains, rods) hurts like the
  machine itself, so nothing on a machine can be driven through.
- **No clipping decorations:** a purely decorative spinner that still sweeps through something solid is taken out.
- **Clear the sweeps:** small fixed scenery that a machine moves through (a post beside a turntable, a wall a blade
  passes) is removed. The road, checkpoints and big structure are never removed. A harmless show machine (a gear
  platform) that would turn through road is stopped instead.
- **Solid scenery:** scenery you can reach (posts, poles, bollards, lamps) is solid.

To run the audit:

```bash
python3 generator/audit.py generator out.rbxl 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20
```

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
