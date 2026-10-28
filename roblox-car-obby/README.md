# Car obby: 100 redesigned levels

`good-redesigned.rbxl` is the uploaded place with all 100 levels in `ServerStorage.OBBY_POOL` (L001–L100) rebuilt from scratch. The packed boot course in `Workspace` (OBBY1–OBBY10) and `RACING_START.CoursePath` are rebuilt from the new levels 1–10. Nothing outside the levels is touched: scripts, lobby, garage, stadium and UI are unchanged.

`levels.json` lists every level's title, world and obstacle sections.

## What each level is made of

- **25 worlds** (neon city, candy, volcano, glacier, jungle, desert, space, synthwave, ocean, haunted, golden temple, factory, cloud kingdom, crystal cavern, aurora, toxic, sakura, arcade, storm, sunset strip, deep sea, mars, royal, matrix, rainbow). Each world is used four times with different glow colours, scenery mix, time of day and set piece.
- **34 obstacle sections**: gap jumps, launch-pad island hopping, kicker ramps, big drops, pad tower climbs, zigzag beams, weaving beams, coaster ribbons, banked sweepers, half-pipe, camelback hills, drop-off stairs, spinning bars, swinging hammers, side rams, crushers, timed laser gates, sweeping floor lasers (jump them), crumbling floors, sideways conveyors, black ice, pinball bumpers, sliding bridges, piston wave road, holey turntable, windmill blades, lava causeway, split routes, slalom gates, moving doors, mud bogs, and boost runways.
- Every level has its own title gate, one landmark set piece, its own lighting (`ObbyLook` + `Lt_*`), and 6–10 checkpoints. No two levels share an obstacle sequence.

All mechanics use the systems the place already has: `ObbyHazard` (Knock, Crush, Burn, Zap, Slip, Slow), `PropMotion` rigs (Spin, Hinge, Slide), `ObbyCrumble`, `Conveyor`, exact `CarLaunchPad`s, `BoostStack` strips, `CarObbyCheckpoint` + `CHECKPOINT_FLAG`, and `HazardKill` floors.

Every level keeps its original `Length` and starts and ends on the course centre line at road height, so the WorldRotation / ObbyAssembler shuffle and the stadium placement work exactly as before.

## Rebuilding

The generator is plain Python 3 (`pip install lz4 zstandard numpy`):

```bash
python3 generator/cache.py generator place.rbxl place.pkl
```

```bash
python3 generator/build.py generator place.pkl out.rbxl
```

```bash
EXPORT_DIR=preview python3 generator/build.py generator place.pkl out.rbxl && python3 generator/validate.py preview
```

`levels.py` holds the 100 level recipes, `sections.py` the obstacle library, `themes.py` the worlds, and `decor.py` / `landmarks.py` the scenery. `validate.py` checks road under the racing line, jumps at three speeds, line obstructions, checkpoint safety, kill floors and slopes.
