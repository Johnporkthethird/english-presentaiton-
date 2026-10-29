"""A prop gallery (GALLERY=1 builds it in place of level 1): every landmark and platform in a row, for close-up renders."""
import skins
import epic_marks as M
from builder import X0, Y0, ZC


def build(r, sk, rng):
    b = r.b
    S = {i: skins.SKINS[i]() for i in range(1, 11)}
    u = [400.0, -600.0]
    out = []

    def slot(label, width, height, fn):
        if u[0] + width > 5000:
            u[0], u[1] = 400.0, u[1] - 900.0
        c = (X0 + u[0] + width / 2, Y0, ZC + u[1])
        fn(c)
        b.pieces.append((label, [c[0] - width / 2, Y0, c[2] - width / 2], [c[0] + width / 2, Y0 + height, c[2] + width / 2]))
        u[0] += width + 120
        out.append(label)

    slot("cake", 320, 260, lambda c: M.cake(b, c, [(150, Y0, Y0 + 120, (226, 170, 110), (255, 150, 190)),
                                                    (110, Y0 + 120, Y0 + 200, (250, 236, 210), (255, 255, 255)),
                                                    (70, Y0 + 200, Y0 + 252, (226, 170, 110), (120, 220, 200))], rng))
    slot("teddy", 300, 520, lambda c: M.teddy(b, c, 260, yaw=3.1416))
    slot("duck", 260, 260, lambda c: M.duck(b, c, 200, yaw=3.1416 + 0.8))
    slot("top", 220, 220, lambda c: M.spinning_top(b, c, 180, S[6].BRICKS))
    slot("blocks", 200, 330, lambda c: [M.toy_block(b, (c[0] + j * 20, Y0 + j * 100, c[2] + j * 12), 100 - j * 10,
                                                     S[6].BRICKS[j], yaw=0.3 * j) for j in range(3)])
    slot("burger", 300, 330, lambda c: M.burger(b, c, 120, rng, k=1.2))
    slot("milkshake", 300, 560, lambda c: M.milkshake(b, c, 110, 330, rng))
    slot("fries", 200, 300, lambda c: M.fry_box(b, c, 140, 200, rng))
    slot("mushroom", 220, 360, lambda c: M.giant_mushroom(b, c, 290, 150, (190, 40, 50), rng))
    slot("chess", 700, 280, lambda c: [M.chess_piece(b, k, (c[0] - 300 + i * 120, Y0, c[2]), 100,
                                                     S[4].WHITE if i % 2 else S[4].BLACK)
                                       for i, k in enumerate(("pawn", "rook", "knight", "bishop", "queen", "king"))])
    slot("tower", 300, 600, lambda c: M.clock_tower(b, c, 170, Y0 + 560, S[5], rng))
    slot("clock", 360, 260, lambda c: (S[5].helix_core(b, (c[0], Y0, c[2]), Y0, Y0 + 200, 110, 40, False),
                                       M.clock_face(b, c, 130, Y0 + 230, S[5], rng)))
    slot("planet", 400, 380, lambda c: M.planet(b, (c[0], Y0 + 190, c[2]), 150, (90, 140, 220), (200, 230, 255), rng,
                                                ring=(260, 0.3, (220, 200, 255))))
    slot("asteroid", 160, 160, lambda c: M.asteroid(b, (c[0], Y0 + 70, c[2]), 120, rng))
    slot("mountain", 700, 520, lambda c: M.mountain(b, c, 300, 500, rng, S[9]))
    slot("pines", 300, 240, lambda c: [M.pine(b, (c[0] - 100 + i * 100, Y0, c[2]), 200 - i * 30, rng) for i in range(3)])
    slot("arcade", 600, 700, lambda c: (M.cabinet(b, c, 400, 600, 200, S[10], yaw=3.1416), M.coin(b, (c[0] + 260, Y0 + 80, c[2]), 110),
                                        M.ghost(b, (c[0] - 260, Y0 + 80, c[2] - 60), 13, S[10].NEON[0])))
    slot("spire", 160, 260, lambda c: M.obsidian_spire(b, c, 250, 40, S[8]))
    slot("canes", 300, 260, lambda c: (M.candy_cane(b, (c[0] - 80, Y0, c[2]), 200, 16), M.lollipop(b, (c[0] + 80, Y0, c[2]), 160, 90, (255, 120, 170), rng)))
    import rush2 as R2
    slot("cupcake", 260, 300, lambda c: M.big_cupcake(b, c, 280, (255, 140, 185), rng))
    slot("ketchup", 160, 330, lambda c: M.ketchup(b, c, 60, 320))
    slot("bounce mushroom", 260, 360, lambda c: M.giant_mushroom(b, c, 230, 150, (150, 70, 210), rng))
    slot("great tree", 700, 800, lambda c: M.great_tree(b, c, 60, Y0, Y0 + 480, rng, S[3]))
    slot("castle", 420, 380, lambda c: M.castle(b, c, 260, 200, 260, rng))
    slot("ufo", 160, 120, lambda c: R2.ufo(b, b.model("UFO", b.scenery), (c[0], Y0 + 60, c[2])))
    slot("gear", 380, 380, lambda c: M.gear(b, (c[0], Y0 + 180, c[2]), 160, (0, 0, 1), S[5].BRASS))
    slot("snowball", 100, 100, lambda c: (R2.ball(b, "Snowball", (c[0], Y0 + 15, c[2]), 30, (245, 250, 255), "Snow", b.scenery),
                                          R2.ball(b, "SnowballLump", (c[0] + 2, Y0 + 25, c[2] + 3), 15, (245, 250, 255), "Snow", b.scenery)))
    slot("crater", 900, 400, lambda c: R2.crater(b, (c[0], Y0, c[2]), 340, Y0, Y0 + 300, rng, gap=(0, 0, 1), gap_deg=40))
    import obby as OB
    from geom import CF as _CF

    def trap(fn):
        def go(c):
            Pt = __import__("skins").Pt
            Pt(b, "Deck", _CF((c[0], Y0 - 2, c[2])), (90, 4, 60), (90, 90, 100), "SmoothPlastic", b.roads, collide=True)
            fn(b, (c[0], Y0, c[2]), 60, 0)
        return go
    for name, fn in (("saw blade", OB.saw), ("pusher", OB.pusher), ("electric floor", OB.zap_floor),
                     ("swinging blade", OB.axe), ("flame jets", OB.flames), ("spring mines", OB.mine), ("claw", OB.claw),
                     ("crusher", OB.crusher), ("sweeper", OB.sweeper)):
        slot(name, 160, 90, trap(fn))
    return out
