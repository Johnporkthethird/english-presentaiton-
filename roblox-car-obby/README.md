# Car obby: 100 parkour levels

`good-redesigned.rbxl` is the uploaded place with all 100 levels in `ServerStorage.OBBY_POOL` (L001-L100) rebuilt as clean parkour courses. The boot course in `Workspace` (OBBY1-OBBY10) and `RACING_START.CoursePath` are rebuilt from the new levels 1-10. Scripts, lobby, garage, stadium and UI are unchanged.

`levels.json` lists every level's title, style and modules in order.

## How the levels are built

- No scenery. Only the course: two-tone platforms, pillars and cubes with neon trim, one palette per level (10 material styles x 100 hues).
- Most jumps are exact launch pads (`CarLaunchPad` + `LaunchExact`), so a hop lands in the same place at any car speed. Modules are joined by pad hops that change height, and each level ends on a pillar-hop finale.
- 28 modules: pillar bounce, cube climb / descent, big-air kicker through hoops, ring drop, windmill launch, loop-de-loop, double loop, barrel roll, wall ride, glass pipe (with a spinning bar), corkscrew, spiral, half-pipe, rotating cross, spinning bridges, sweeper discs, holey turntable, swinging platforms, sliding bridges, piston wave, crushers, laser rhythm gates, laser limbo beam, moving doors, crumbling checkerboard, tilt runs, zigzag beams.
- Each level has a signature module that appears twice, plus a flight, a rotating, a stunt and a skill module. No two levels share a sequence.
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

`levels2.py` holds the palettes and recipes, `parkour.py` the module kit, `validate.py` the geometry checks (road under the racing line, every pad flight lands, nothing solid on the line, safe checkpoints, kill floors, slopes).
