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
    for i in range(1, 11):
        slot("plat%d" % i, 120, 80, lambda c, i=i: S[i].plat(b, (c[0], Y0 + 60, c[2]), 60, rng))
    return out
