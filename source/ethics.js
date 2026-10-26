const pptxgen = require("pptxgenjs");
const path = require("path");
const { applyTheme } = require("/root/.claude/skills/synced/e5ada5e5-5735-45c5-a288-497db0367b44_0fea8d63-5f60-467a-87f8-204c1ac0cfcc/pptx/scripts/apply_theme.js");
const A = (f) => path.join(__dirname, "assets", f);
const ic = (name, color) => A(`ic-${name}-${color}.png`);

const THEME = {
  name: "NutriPill",
  headFontFace: "Arial Black",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "0B1F3A", lt1: "FFFFFF", dk2: "123A6B", lt2: "EEF6F9",
    accent1: "14C9A1", accent2: "FF6B4A", accent3: "2A6BD1", accent4: "0FA888", accent5: "8FA3B8", accent6: "F4B740",
    hlink: "2A6BD1", folHlink: "123A6B",
  },
};
const HEX = { navy: "0B1F3A", mint: "14C9A1", coral: "FF6B4A", muted: "5B6B80", mutedDark: "B8C7D9" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.title = "NutriPill Workplace Ethics";
pres.author = "Dani, Max, William, Miguel";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

// ---------- Layouts ----------
pres.defineSlideMaster({
  title: "COVER",
  background: { path: A("bg-dark.png") },
  objects: [],
});
const contentLayout = (name, dark) => pres.defineSlideMaster({
  title: name,
  background: { path: A(dark ? "bg-dark.png" : "bg-light.png") },
  objects: [
    { image: { path: A(dark ? "logo-light.png" : "logo-dark.png"), x: 11.35, y: 0.42, w: 1.44, h: 0.4 } },
    { placeholder: { options: { name: "kicker", type: "body", x: 0.6, y: 0.45, w: 8, h: 0.35, fontSize: 13, bold: true, charSpacing: 4, color: C.accent1, margin: 0, valign: "middle" }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.85, w: 10.4, h: 0.95, fontSize: 36, bold: true, align: "left", fontFace: THEME.headFontFace, color: dark ? C.background1 : C.text1, margin: 0, valign: "middle" }, text: "" } },
  ],
  slideNumber: { x: 12.3, y: 6.95, w: 0.5, h: 0.3, fontSize: 10, color: dark ? "8FA3B8" : "8FA3B8", align: "right" },
});
contentLayout("LIGHT", false);
contentLayout("DARK", true);

// ---------- helpers ----------
const shadow = () => ({ type: "outer", color: "0B1F3A", blur: 18, offset: 6, angle: 90, opacity: 0.12 });
const T = (slide, text, opts) => slide.addText(text, { isTextBox: true, fontFace: THEME.bodyFontFace, margin: 0, valign: "top", ...opts });
const iconCircle = (slide, name, x, y, d, fill, iconColor, anim) => {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { type: "none" }, objectName: `${anim}_circle` });
  const p = d * 0.27;
  slide.addImage({ path: ic(name, iconColor), x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p, objectName: `${anim}_icon`, altText: name });
};
const card = (slide, x, y, w, h, fill, anim, extra = {}) =>
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.18, fill: { color: fill, ...extra.fill }, line: extra.line || { type: "none" }, shadow: extra.noShadow ? undefined : shadow(), objectName: `${anim}_card` });


let s = pres.addSlide({ masterName: "DARK" });
s.addText("Workplace Ethics & Social Responsibility", { placeholder: "title" });

// centrepiece
const CX = 6.667, CY = 4.25, R = 2.05;
s.addImage({ path: A("ethics-hero.png"), x: CX - R, y: CY - R, w: 2 * R, h: 2 * R, objectName: "a1_hero", altText: "NutriPill capsule inside glowing rings" });

const glass = (x, y, w, h, anim) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.2, fill: { color: "FFFFFF", transparency: 91 }, line: { color: "FFFFFF", transparency: 78, width: 1 }, objectName: `${anim}_glass` });
const connector = (x1, x2, y, col, anim) => {
  s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y, w: Math.abs(x2 - x1), h: 0, line: { color: col, width: 1.5, dashType: "dash" }, objectName: `${anim}_line` });
  const dx = x1 < x2 ? x2 : x2;
  s.addShape(pres.shapes.OVAL, { x: dx - 0.09, y: y - 0.09, w: 0.18, h: 0.18, fill: { color: col }, line: { color: "FFFFFF", width: 1.5 }, objectName: `${anim}_node` });
};

const CW = 3.85, CH = 1.95, LX = 0.6, RX = 13.333 - 0.6 - CW, Y1 = 2.2, Y2 = 4.35;
const items = [
  [LX, Y1, "friends", "01", "Same job, same pay", "Men and women doing the same job earn the same. We hire for skills, never for gender or race.", HEX.mint, "navy"],
  [LX, Y2, "comments", "02", "Everyone has a voice", "Once a month, anyone, from the newest worker to the CEO, can pitch an idea to improve NutriPill.", "2E9E5B", "white"],
  [RX, Y1, "euro", "03", "Nobody priced out", "Just €9.99 a month, plus 20% off with a student card, so anyone can try it.", HEX.coral, "white"],
];
items.forEach(([x, y, icn, num, h, d, col, icol], i) => {
  const a = `a${2 + i}`;
  glass(x, y, CW, CH, a);
  s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: y + 0.3, w: 0.66, h: 0.66, fill: { color: col }, line: { type: "none" }, shadow: { type: "outer", color: col, blur: 16, offset: 0, angle: 90, opacity: 0.6 }, objectName: `${a}_disc` });
  s.addImage({ path: ic(icn, icol), x: x + 0.46, y: y + 0.46, w: 0.34, h: 0.34, objectName: `${a}_icon`, altText: h });
  T(s, [{ text: num, options: { color: col, bold: true, fontSize: 12, charSpacing: 2, breakLine: true } }, { text: h, options: { color: "FFFFFF", bold: true, fontSize: 17 } }], { x: x + 1.12, y: y + 0.26, w: CW - 1.3, h: 0.74, valign: "middle", objectName: `${a}_h` });
  T(s, d, { x: x + 0.3, y: y + 1.1, w: CW - 0.55, h: 0.75, fontSize: 14, color: HEX.mutedDark, objectName: `${a}_d` });
  // connector to the orbit
  const my = y + CH / 2, dy = Math.abs(my - CY), ox = Math.sqrt(R * 0.864 * R * 0.864 - dy * dy);
  if (x < CX) connector(x + CW, CX - ox, my, col, a); else connector(CX + ox, x, my, col, a);
});

// quote card (bottom right), brand mint
const qx = RX, qy = Y2;
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: qx, y: qy, w: CW, h: CH, rectRadius: 0.2, fill: { color: HEX.mint }, line: { type: "none" }, shadow: { type: "outer", color: HEX.mint, blur: 24, offset: 0, angle: 90, opacity: 0.45 }, objectName: "a5_card" });
s.addImage({ path: ic("quote", "navy"), x: qx + 0.3, y: qy + 0.25, w: 0.38, h: 0.38, objectName: "a5_q", altText: "" });
T(s, "If our team isn't happy, our customers won't be either.", { x: qx + 0.3, y: qy + 0.68, w: CW - 0.55, h: 0.75, fontSize: 17, bold: true, color: HEX.navy, objectName: "a5_t" });
s.addImage({ path: A("logo-mark.png"), x: qx + 0.24, y: qy + 1.4, w: 0.45, h: 0.45, objectName: "a5_mark", altText: "NutriPill logo" });
T(s, [{ text: "William", options: { bold: true } }, { text: "  ·  HR Manager", options: {} }], { x: qx + 0.75, y: qy + 1.43, w: 2.6, h: 0.4, fontSize: 14, color: HEX.navy, valign: "middle", objectName: "a5_sig" });
{ const my = qy + CH / 2, dy = Math.abs(my - CY), ox = Math.sqrt(R * 0.864 * R * 0.864 - dy * dy); connector(CX + ox, qx, my, HEX.mint, "a5"); }

// slogan ribbon under the capsule
const SW = 6.5, SX = CX - SW / 2, SY = 6.62;
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: SX, y: SY, w: SW, h: 0.5, rectRadius: 0.25, fill: { color: "0B1F3A" }, line: { color: HEX.mint, width: 1.25 }, objectName: "a6_chip" });
s.addImage({ path: ic("lock", "mint"), x: SX + 0.22, y: SY + 0.12, w: 0.26, h: 0.26, objectName: "a6_lock", altText: "lock" });
T(s, [{ text: "Everyone can ", options: { color: "FFFFFF" } }, { text: "LOCK IN", options: { color: HEX.mint, bold: true } }, { text: "  ·  1 pill a day keeps the hunger away!", options: { color: "FFFFFF", italic: true } }],
  { x: SX + 0.6, y: SY, w: SW - 0.75, h: 0.5, fontSize: 14, valign: "middle", objectName: "a6_t" });

s.addNotes("As HR Manager, I believe one simple thing: if our team isn't happy, our customers won't be either. So we have three clear rules. First, same job, same pay. Men and women who do the same job earn exactly the same, and we hire people for their skills, never because of their gender or race. Second, everyone has a voice. Once a month, anyone in the company, from the newest worker to the CEO, can pitch an idea to improve NutriPill. That's how we keep innovation alive. And third, nobody is priced out. Our social responsibility includes our customers too, so NutriPill costs just 9.99 a month, and students get 20% off with their student card. That way, anyone can try it and, as our slogan says, lock in.");

(async () => {
  const out = path.join(__dirname, "Ethics-slide.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("wrote", out);
})();
