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
pres.title = "NutriPill HR slide";
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
s.addText("How We Build Our Team", { placeholder: "title" });
T(s, "Finding the right people, and keeping them motivated.", { x: 0.6, y: 1.85, w: 9, h: 0.45, fontSize: 18, color: HEX.mutedDark, objectName: "a1_sub" });

// left: hiring process
T(s, "OUR HIRING PROCESS", { x: 0.6, y: 2.55, w: 5.8, h: 0.35, fontSize: 13, bold: true, charSpacing: 3, color: HEX.mint, objectName: "a2_h" });
s.addShape(pres.shapes.LINE, { x: 1.0, y: 3.4, w: 0, h: 2.2, line: { color: HEX.mint, width: 2, dashType: "dash" }, objectName: "a2_line" });
const steps = [
  ["file", "1. Apply", "Send your CV and a short video explaining why you want to join NutriPill."],
  ["comments", "2. Live interview", "A real conversation about how you deal with pressure and teamwork."],
  ["usercheck", "3. Trial day", "Spend a day working with the team before we both decide."],
];
steps.forEach(([icn, h, d], i) => {
  const y = 3.0 + i * 1.15;
  s.addShape(pres.shapes.OVAL, { x: 0.6, y, w: 0.8, h: 0.8, fill: { color: HEX.mint }, line: { type: "none" }, objectName: `a${3 + i}_dot` });
  s.addImage({ path: ic(icn, "navy"), x: 0.8, y: y + 0.2, w: 0.4, h: 0.4, objectName: `a${3 + i}_icon`, altText: h });
  T(s, h, { x: 1.65, y: y - 0.02, w: 4.9, h: 0.4, fontSize: 19, bold: true, color: "FFFFFF", objectName: `a${3 + i}_h` });
  T(s, d, { x: 1.65, y: y + 0.38, w: 4.9, h: 0.65, fontSize: 14, color: HEX.mutedDark, objectName: `a${3 + i}_d` });
});

// right: executive board
card(s, 6.95, 2.5, 5.65, 3.85, "FFFFFF", "a6");
T(s, "OUR EXECUTIVE BOARD", { x: 7.3, y: 2.8, w: 5.1, h: 0.35, fontSize: 13, bold: true, charSpacing: 3, color: HEX.coral, objectName: "a6_h" });
const board = [
  ["trophy", "Miguel", "CEO", "Leads the pitch and the company's vision"],
  ["share", "Dani", "CMO", "Runs our advertising and market research"],
  ["coins", "Max", "CFO", "Manages costs, prices and finances"],
  ["users", "William", "HR Manager", "Hires our team and looks after our culture"],
];
board.forEach(([icn, name, role, d], i) => {
  const y = 3.3 + i * 0.75;
  s.addShape(pres.shapes.OVAL, { x: 7.3, y: y + 0.05, w: 0.55, h: 0.55, fill: { color: i === 3 ? HEX.coral : HEX.navy }, line: { type: "none" }, objectName: `a${7 + i}_dot` });
  s.addImage({ path: ic(icn, i === 3 ? "white" : "mint"), x: 7.45, y: y + 0.2, w: 0.25, h: 0.25, objectName: `a${7 + i}_icon`, altText: role });
  T(s, [{ text: name, options: { bold: true, color: HEX.navy } }, { text: `  ·  ${role}`, options: { bold: true, color: HEX.mint } }], { x: 8.05, y: y - 0.02, w: 4.4, h: 0.35, fontSize: 16, objectName: `a${7 + i}_n` });
  T(s, d, { x: 8.05, y: y + 0.33, w: 4.4, h: 0.32, fontSize: 14, color: HEX.muted, objectName: `a${7 + i}_d` });
});

// bottom: what we offer
T(s, "What we offer:", { x: 0.6, y: 6.6, w: 1.9, h: 0.45, fontSize: 16, bold: true, color: "FFFFFF", valign: "middle", objectName: "a11_h" });
[["graduate", "Training"], ["clock", "Flexible hours"], ["euro", "Fair pay"], ["handshake", "Respect for everyone"]].forEach(([icn, t], i) => {
  const w = [1.65, 2.05, 1.5, 2.6][i], x = [2.5, 4.3, 6.5, 8.15][i];
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 6.6, w, h: 0.45, rectRadius: 0.22, fill: { color: "FFFFFF", transparency: 88 }, line: { color: HEX.mint, width: 1 }, objectName: `a${12 + i}_chip` });
  s.addImage({ path: ic(icn, "mint"), x: x + 0.15, y: 6.7, w: 0.25, h: 0.25, objectName: `a${12 + i}_icon`, altText: t });
  T(s, t, { x: x + 0.48, y: 6.6, w: w - 0.55, h: 0.45, fontSize: 14, bold: true, color: "FFFFFF", valign: "middle", objectName: `a${12 + i}_t` });
});

s.addNotes("As HR Manager, my job is to find the right people for NutriPill and keep them motivated. Our hiring process has three steps. First, you apply by sending your CV and a short video explaining why you want to join us. Second, we do a live interview. It's not just about your CV; we want to see how you deal with pressure and how you work in a team. Finally, there's a trial day, so you can work with the team before we both decide. Right now, our team is the four of us: Miguel is our CEO and leads the company, Dani is our CMO and runs the marketing, Max is our CFO and manages the money, and I'm the HR Manager. In return for their hard work, we offer our team training, flexible hours, fair pay and, of course, respect for everyone.");

(async () => {
  const out = path.join(__dirname, "HR-slide.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("wrote", out);
})();
