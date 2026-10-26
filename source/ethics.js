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

// decorative capsule, bottom-left
s.addImage({ path: A("hero.png"), x: -1.0, y: 5.05, w: 3.9, h: 3.9, transparency: 20, objectName: "a1_deco", altText: "" });

// left: statement
T(s, "HOW WE WORK", { x: 0.6, y: 2.05, w: 5, h: 0.35, fontSize: 13, bold: true, charSpacing: 4, color: HEX.mint, objectName: "a2_k" });
T(s, [
  { text: "At NutriPill, how we treat people ", options: { color: "FFFFFF" } },
  { text: "matters as much as", options: { color: HEX.mint } },
  { text: " what we sell.", options: { color: "FFFFFF" } },
], { x: 0.6, y: 2.45, w: 5.1, h: 1.9, fontSize: 30, bold: true, objectName: "a3_quote" });
s.addImage({ path: A("logo-mark.png"), x: 0.55, y: 4.55, w: 0.7, h: 0.7, objectName: "a4_mark", altText: "NutriPill logo" });
T(s, [{ text: "William", options: { bold: true, color: "FFFFFF", breakLine: true } }, { text: "HR Manager, NutriPill", options: { color: HEX.mutedDark } }],
  { x: 1.4, y: 4.55, w: 3.5, h: 0.7, fontSize: 15, valign: "middle", objectName: "a4_sig" });

// right: three capsule-shaped commitments
const items = [
  ["friends", "Respect for everyone", "Everyone is treated with respect, whatever their gender or race. No exceptions.", HEX.mint, "navy"],
  ["shield", "Living our values", "Our team follows our core values: innovation, caring for the planet and accessibility.", "2E9E5B", "white"],
  ["euro", "Prices for every pocket", "NutriPill is affordable for all income groups, so everyone can try it.", HEX.coral, "white"],
];
items.forEach(([icn, h, d, col, icol], i) => {
  const x = 6.15, y = 2.05 + i * 1.45, w = 6.45, hh = 1.2, r = hh / 2;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: hh, rectRadius: r, fill: { color: "FFFFFF" }, line: { type: "none" }, shadow: { type: "outer", color: "000000", blur: 18, offset: 6, angle: 90, opacity: 0.3 }, objectName: `a${5 + i}_body` });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 1.7, h: hh, rectRadius: r, fill: { color: col }, line: { type: "none" }, objectName: `a${5 + i}_half` });
  s.addShape(pres.shapes.RECTANGLE, { x: x + 1.1, y, w: 0.6, h: hh, fill: { color: col }, line: { type: "none" }, objectName: `a${5 + i}_halfsq` });
  s.addShape(pres.shapes.LINE, { x: x + 1.7, y, w: 0, h: hh, line: { color: "0B1F3A", width: 1, transparency: 85 }, objectName: `a${5 + i}_seam` });
  s.addImage({ path: ic(icn, icol), x: x + 0.62, y: y + 0.36, w: 0.48, h: 0.48, objectName: `a${5 + i}_icon`, altText: h });
  T(s, h, { x: x + 1.95, y: y + 0.14, w: 4.25, h: 0.4, fontSize: 19, bold: true, color: HEX.navy, objectName: `a${5 + i}_h` });
  T(s, d, { x: x + 1.95, y: y + 0.54, w: 4.25, h: 0.55, fontSize: 14, color: HEX.muted, objectName: `a${5 + i}_d` });
});

// bottom: slogan chip
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.15, y: 6.45, w: 6.45, h: 0.55, rectRadius: 0.27, fill: { color: HEX.mint, transparency: 85 }, line: { color: HEX.mint, width: 1.25 }, objectName: "a8_chip" });
s.addImage({ path: ic("lock", "mint"), x: 6.4, y: 6.58, w: 0.29, h: 0.29, objectName: "a8_lock", altText: "lock" });
T(s, [{ text: "Everyone can ", options: { color: "FFFFFF" } }, { text: "LOCK IN", options: { color: HEX.mint, bold: true } }, { text: ": 1 pill a day keeps the hunger away!", options: { color: "FFFFFF", italic: true } }],
  { x: 6.85, y: 6.45, w: 5.6, h: 0.55, fontSize: 15, valign: "middle", objectName: "a8_t" });

s.addNotes("As HR Manager, I'm responsible for how people work together at NutriPill, because for us, how we treat people matters as much as what we sell. Our workplace ethics are based on three ideas. First, respect for everyone: every employee is treated with respect, whatever their gender or race, with no exceptions. Second, living our values: we expect our team to follow our core values, which are innovation, caring for the planet and accessibility. And third, our social responsibility doesn't stop with our employees, it includes our customers too. That's why NutriPill is affordable for all income groups, so that everyone can try it and, as our slogan says, lock in.");

(async () => {
  const out = path.join(__dirname, "Ethics-slide.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("wrote", out);
})();
