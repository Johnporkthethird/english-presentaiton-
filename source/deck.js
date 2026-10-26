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
pres.title = "NutriPill";
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
const T = (slide, text, opts) => slide.addText(text, { isTextBox: true, fontFace: THEME.bodyFontFace, margin: 0, ...opts });
const iconCircle = (slide, name, x, y, d, fill, iconColor, anim) => {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { type: "none" }, objectName: `${anim}_circle` });
  const p = d * 0.27;
  slide.addImage({ path: ic(name, iconColor), x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p, objectName: `${anim}_icon`, altText: name });
};
const card = (slide, x, y, w, h, fill, anim, extra = {}) =>
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.18, fill: { color: fill, ...extra.fill }, line: extra.line || { type: "none" }, shadow: extra.noShadow ? undefined : shadow(), objectName: `${anim}_card` });

// ================= 1. COVER =================
pres.addSection({ title: "Welcome" });
let s = pres.addSlide({ masterName: "COVER", sectionTitle: "Welcome" });
s.addImage({ path: A("hero.png"), x: 6.9, y: 0.35, w: 6.8, h: 6.8, objectName: "a1_hero", altText: "NutriPill capsule illustration" });
s.addImage({ path: A("logo-light.png"), x: 0.75, y: 0.65, w: 2.3, h: 0.64, objectName: "a2_logo", altText: "NutriPill logo" });
T(s, "ENGLISH PRESENTATION  ·  BUSINESS PROPOSAL", { x: 0.8, y: 2.15, w: 6.5, h: 0.35, fontSize: 13, bold: true, charSpacing: 4, color: HEX.mint, objectName: "a3_kicker" });
T(s, [{ text: "Nutri", options: { color: "FFFFFF" } }, { text: "Pill", options: { color: HEX.mint } }], { x: 0.75, y: 2.5, w: 6.5, h: 1.5, fontSize: 80, bold: true, fontFace: THEME.headFontFace, objectName: "a4_title" });
T(s, "Essential nutrients. Anytime. Anywhere.", { x: 0.8, y: 4.0, w: 6.2, h: 0.55, fontSize: 24, color: "FFFFFF", italic: true, objectName: "a5_tag" });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.8, y: 5.25, w: 4.9, h: 0.6, rectRadius: 0.3, fill: { color: "FFFFFF", transparency: 88 }, line: { color: "FFFFFF", transparency: 70, width: 1 }, objectName: "a6_pill" });
T(s, "By Dani, Max, William & Miguel", { x: 0.8, y: 5.25, w: 4.9, h: 0.6, fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle", objectName: "a6_names" });
s.addNotes("Hi everyone! We are Dani, Max, William and Miguel, and today we are going to present our business idea: NutriPill. Essential nutrients — anytime, anywhere.");

// ================= 2. INTRODUCTION =================
pres.addSection({ title: "The idea" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "The idea" });
s.addText("INTRODUCTION", { placeholder: "kicker" });
s.addText("Have you ever been too busy to eat?", { placeholder: "title" });
s.addImage({ path: A("hero-light.png"), x: 8.15, y: 2.05, w: 4.6, h: 4.6, objectName: "a1_art", altText: "Capsule illustration" });
T(s, "Imagine a pill that provides essential nutrients when you don't have time for a meal.", { x: 0.6, y: 2.25, w: 6.9, h: 1.3, fontSize: 24, color: HEX.navy, objectName: "a2_text" });
card(s, 0.6, 3.95, 6.9, 2.55, "FFFFFF", "a3");
s.addImage({ path: A("logo-dark.png"), x: 0.95, y: 4.25, w: 2.16, h: 0.6, objectName: "a3_logo", altText: "NutriPill logo" });
T(s, "A convenient way to get essential nutrients on the go — designed for your busy lifestyle.", { x: 0.95, y: 4.95, w: 6.2, h: 0.75, fontSize: 16, color: HEX.muted, objectName: "a3_text" });
[["Small", 0.95], ["Simple", 2.45], ["On the go", 3.95]].forEach(([t, x], i) => {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 5.8, w: 1.35, h: 0.45, rectRadius: 0.22, fill: { color: "E3FAF4" }, line: { type: "none" }, objectName: `a${4 + i}_chip` });
  T(s, t, { x, y: 5.8, w: 1.35, h: 0.45, fontSize: 14, bold: true, color: "0FA888", align: "center", valign: "middle", objectName: `a${4 + i}_chiptext` });
});
s.addNotes("Have you ever been too busy to eat? Imagine a pill that gives you essential nutrients when you don't have time for a meal. Meet NutriPill: small, simple, and designed for your busy lifestyle.");

// ================= 3. THE PROBLEM =================
s = pres.addSlide({ masterName: "DARK", sectionTitle: "The idea" });
s.addText("THE PROBLEM", { placeholder: "kicker" });
s.addText("No time to eat properly", { placeholder: "title" });
T(s, "Busy schedules mean many students and workers skip meals because they are always in a hurry.", { x: 0.6, y: 2.1, w: 8.5, h: 0.9, fontSize: 20, color: HEX.mutedDark, objectName: "a1_text" });
const probs = [
  ["battery", "Low energy", "Skipping meals leaves you tired before the day is over."],
  ["brain", "Poor focus", "It becomes harder to concentrate in class or at work."],
  ["apple", "Poor nutrition", "Your body misses the nutrients it needs every day."],
];
probs.forEach(([icn, h, d], i) => {
  const x = 0.6 + i * 4.1;
  card(s, x, 3.3, 3.8, 2.45, "FFFFFF", `a${2 + i}`, { fill: { transparency: 92 }, line: { color: "FFFFFF", transparency: 80, width: 1 }, noShadow: true });
  iconCircle(s, icn, x + 0.35, 3.6, 0.8, HEX.coral, "white", `a${2 + i}`);
  T(s, h, { x: x + 0.35, y: 4.55, w: 3.1, h: 0.45, fontSize: 20, bold: true, color: "FFFFFF", objectName: `a${2 + i}_h` });
  T(s, d, { x: x + 0.35, y: 5.0, w: 3.1, h: 0.65, fontSize: 14, color: HEX.mutedDark, objectName: `a${2 + i}_d` });
});
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 6.05, w: 12.0, h: 0.65, rectRadius: 0.32, fill: { color: HEX.mint }, line: { type: "none" }, objectName: "a5_bar" });
T(s, "They need a quick and convenient way to get essential nutrients.", { x: 0.6, y: 6.05, w: 12.0, h: 0.65, fontSize: 18, bold: true, color: HEX.navy, align: "center", valign: "middle", objectName: "a5_bartext" });
s.addNotes("Nowadays many people have very busy schedules. Students and workers often skip meals because they are in a hurry. This leads to low energy, difficulty concentrating and poor nutrition. They need a quick and convenient way to get essential nutrients.");

// ================= 4. OUR SOLUTION =================
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "The idea" });
s.addText("OUR SOLUTION", { placeholder: "kicker" });
s.addText("Meet NutriPill", { placeholder: "title" });
s.addImage({ path: A("hero-light.png"), x: 0.45, y: 2.0, w: 4.4, h: 4.4, objectName: "a1_art", altText: "Capsule illustration" });
const feats = [
  ["lightbulb", "Innovative", "A new way to get essential nutrients in seconds."],
  ["suitcase", "Small & portable", "Easy to carry in your bag or pocket."],
  ["bolt", "Keeps you going", "Helps you maintain your energy all day."],
  ["heart", "Built for busy days", "Perfect for students and workers."],
];
feats.forEach(([icn, h, d], i) => {
  const x = 5.3 + (i % 2) * 3.8, y = 2.05 + Math.floor(i / 2) * 1.85;
  card(s, x, y, 3.5, 1.6, "FFFFFF", `a${2 + i}`);
  iconCircle(s, icn, x + 0.25, y + 0.3, 0.7, "E3FAF4", "mint", `a${2 + i}`);
  T(s, h, { x: x + 1.15, y: y + 0.25, w: 2.2, h: 0.4, fontSize: 17, bold: true, color: HEX.navy, objectName: `a${2 + i}_h` });
  T(s, d, { x: x + 1.15, y: y + 0.65, w: 2.2, h: 0.75, fontSize: 14, color: HEX.muted, objectName: `a${2 + i}_d` });
});
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.3, y: 5.85, w: 7.3, h: 0.85, rectRadius: 0.15, fill: { color: "FFF0EC" }, line: { type: "none" }, objectName: "a6_note" });
T(s, [{ text: "Good to know: ", options: { bold: true, color: HEX.coral } }, { text: "NutriPill doesn't replace a complete meal — it supplements your nutrition when life gets busy.", options: { color: HEX.navy } }],
  { x: 5.55, y: 5.85, w: 6.9, h: 0.85, fontSize: 14, valign: "middle", objectName: "a6_notetext" });
s.addNotes("NutriPill is an innovative and convenient pill that provides essential nutrients when people don't have time to eat. It is small, easy to carry, and perfect for busy students and workers. Our goal is to help people keep their energy up. It doesn't replace a complete meal, but it's a practical way to supplement nutrition when life gets busy.");

// ================= 5. TARGET AUDIENCE =================
s = pres.addSlide({ masterName: "DARK", sectionTitle: "The idea" });
s.addText("TARGET AUDIENCE", { placeholder: "kicker" });
s.addText("Who is NutriPill for?", { placeholder: "title" });
T(s, "Busy people who don't always have time to eat properly.", { x: 0.6, y: 2.0, w: 9, h: 0.6, fontSize: 20, color: HEX.mutedDark, objectName: "a1_text" });
const aud = [
  ["grad", "Students", "Long days of classes, exams and homework."],
  ["briefcase", "Workers", "Meetings, deadlines and no lunch break."],
  ["run", "Athletes", "Extra nutrients for training days."],
  ["clock", "Hectic lifestyles", "Anyone who is always on the move."],
];
aud.forEach(([icn, h, d], i) => {
  const x = 0.6 + i * 3.08;
  card(s, x, 3.0, 2.8, 3.4, "FFFFFF", `a${2 + i}`);
  iconCircle(s, icn, x + 0.85, 3.35, 1.1, HEX.mint, "white", `a${2 + i}`);
  T(s, h, { x: x + 0.2, y: 4.7, w: 2.4, h: 0.5, fontSize: 20, bold: true, color: HEX.navy, align: "center", objectName: `a${2 + i}_h` });
  T(s, d, { x: x + 0.25, y: 5.2, w: 2.3, h: 0.9, fontSize: 14, color: HEX.muted, align: "center", objectName: `a${2 + i}_d` });
});
s.addNotes("NutriPill is designed for busy people who don't always have time to eat properly. Our main target audience is students, workers, athletes, and people with hectic lifestyles who need a quick way to supplement their nutrition during the day.");

// ================= 6. ACTION PLAN =================
pres.addSection({ title: "The business" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "The business" });
s.addText("ACTION PLAN", { placeholder: "kicker" });
s.addText("Three pillars of our business model", { placeholder: "title" });
const pillars = [
  ["coins", "Revenue", "Direct sales of NutriPill plus brand experiences linked to the product."],
  ["share", "Channels", "A strong presence on the main social networks, plus in-person experiences."],
  ["tag", "Pricing", "Affordable but with added value: an accessible premium option."],
];
pillars.forEach(([icn, h, d], i) => {
  const x = 0.6 + i * 4.1;
  card(s, x, 2.25, 3.8, 4.35, "FFFFFF", `a${1 + i}`);
  T(s, `0${i + 1}`, { x: x + 2.4, y: 2.45, w: 1.2, h: 0.8, fontSize: 40, fontFace: THEME.headFontFace, color: "C8F0E5", align: "right", objectName: `a${1 + i}_num` });
  iconCircle(s, icn, x + 0.4, 2.6, 1.0, HEX.navy, "mint", `a${1 + i}`);
  T(s, h, { x: x + 0.4, y: 3.9, w: 3.0, h: 0.55, fontSize: 24, bold: true, color: HEX.navy, objectName: `a${1 + i}_h` });
  T(s, d, { x: x + 0.4, y: 4.5, w: 3.0, h: 1.2, fontSize: 16, color: HEX.muted, objectName: `a${1 + i}_d` });
});
// social logos on the Channels card
["instagram", "tiktok", "youtube"].forEach((n, j) => {
  s.addImage({ path: ic(n, "navy"), x: 4.7 + 0.1 + j * 0.65, y: 5.85, w: 0.42, h: 0.42, objectName: "a2_social", altText: n });
});
s.addNotes("Our business model is based on three pillars. Revenue: direct sales and experiences connected to the product. Channels: a strong presence on social media like Instagram, TikTok and YouTube, plus in-person experiences. Pricing: affordable, but with added value — an accessible premium option.");

// ================= 7. GROWTH STRATEGY =================
s = pres.addSlide({ masterName: "DARK", sectionTitle: "The business" });
s.addText("GROWTH STRATEGY", { placeholder: "kicker" });
s.addText("How we will grow", { placeholder: "title" });
s.addShape(pres.shapes.LINE, { x: 1.2, y: 3.15, w: 10.9, h: 0, line: { color: HEX.mint, width: 2, dashType: "dash" }, objectName: "a1_line" });
const steps = [
  ["camera", "Inspiring content", "Social media posts that show a real, healthy lifestyle."],
  ["star", "Local influencers", "Partners who represent the brand's philosophy."],
  ["gift", "Memorable experiences", "Events, personalized kits and collaborations."],
  ["users", "Active community", "Inviting customers to be part of the brand."],
];
steps.forEach(([icn, h, d], i) => {
  const x = 0.6 + i * 3.1, cx = x + 0.6;
  s.addShape(pres.shapes.OVAL, { x: cx - 0.55 + 0.0, y: 2.6, w: 1.1, h: 1.1, fill: { color: HEX.navy }, line: { color: HEX.mint, width: 3 }, objectName: `a${2 + i}_ring` });
  s.addImage({ path: ic(icn, "mint"), x: cx - 0.27, y: 2.88, w: 0.54, h: 0.54, objectName: `a${2 + i}_icon`, altText: h });
  T(s, `0${i + 1}`, { x, y: 4.0, w: 2.8, h: 0.5, fontSize: 22, fontFace: THEME.headFontFace, color: HEX.coral, objectName: `a${2 + i}_num` });
  T(s, h, { x, y: 4.5, w: 2.8, h: 0.5, fontSize: 20, bold: true, color: "FFFFFF", objectName: `a${2 + i}_h` });
  T(s, d, { x, y: 5.05, w: 2.7, h: 0.95, fontSize: 15, color: HEX.mutedDark, objectName: `a${2 + i}_d` });
});
s.addNotes("To grow, we have a four-step strategy. One: create inspiring content on social media showing a real lifestyle. Two: work with local influencers who represent our brand's philosophy. Three: create memorable experiences like events, personalized kits and collaborations. Four: build an active community by inviting customers to be part of the brand.");

// ================= 8. OUR PROPOSAL =================
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "The business" });
s.addText("OUR PROPOSAL", { placeholder: "kicker" });
s.addText("Let's grow together", { placeholder: "title" });
iconCircle(s, "handshake", 0.6, 2.2, 1.2, HEX.mint, "white", "a1");
T(s, "We are looking for brands that want to grow with us.", { x: 0.6, y: 3.65, w: 5.4, h: 0.9, fontSize: 22, bold: true, color: HEX.navy, objectName: "a2_lead" });
T(s, "We propose a strategic partnership where you gain visibility, a strong position with a young audience, and connection with new customers.", { x: 0.6, y: 4.6, w: 5.4, h: 1.5, fontSize: 17, color: HEX.muted, objectName: "a2_text" });
card(s, 6.75, 2.1, 5.85, 4.6, HEX.navy, "a3");
T(s, "WITH YOUR SUPPORT WE CAN:", { x: 7.2, y: 2.45, w: 5, h: 0.4, fontSize: 14, bold: true, charSpacing: 3, color: HEX.mint, objectName: "a3_h" });
["Develop joint products and experiences", "Increase our reach through campaigns", "Build greater credibility and growth"].forEach((t, i) => {
  const y = 3.15 + i * 1.1;
  s.addShape(pres.shapes.OVAL, { x: 7.2, y, w: 0.6, h: 0.6, fill: { color: HEX.mint }, line: { type: "none" }, objectName: `a${4 + i}_dot` });
  s.addImage({ path: ic("check", "navy"), x: 7.35, y: y + 0.15, w: 0.3, h: 0.3, objectName: `a${4 + i}_check`, altText: "check" });
  T(s, t, { x: 8.05, y: y - 0.1, w: 4.3, h: 0.8, fontSize: 18, color: "FFFFFF", valign: "middle", objectName: `a${4 + i}_t` });
});
s.addNotes("We are looking for brands that want to grow with us. We propose a strategic partnership where our partners gain visibility, a strong position with a young audience and connection with new customers. With your support we can develop joint products and experiences, increase our reach through campaigns, and build more credibility and growth.");

// ================= 9. GOALS =================
s = pres.addSlide({ masterName: "DARK", sectionTitle: "The business" });
s.addText("OUR GOALS", { placeholder: "kicker" });
s.addText("What we expect to achieve", { placeholder: "title" });
s.addImage({ path: A("hero.png"), x: 8.3, y: 2.0, w: 4.8, h: 4.8, objectName: "a1_art", altText: "Capsule illustration" });
s.addShape(pres.shapes.LINE, { x: 1.05, y: 2.6, w: 0, h: 3.6, line: { color: HEX.mint, width: 2, dashType: "dash" }, objectName: "a1_line" });
const goals = [
  ["flag", "In 6 months", "Build an active community around NutriPill."],
  ["chart", "In 12 months", "Grow our digital reach and double our customer base."],
  ["trophy", "Long term", "Become a leader in the local market, then expand nationwide."],
];
goals.forEach(([icn, h, d], i) => {
  const y = 2.2 + i * 1.6;
  s.addShape(pres.shapes.OVAL, { x: 0.6, y, w: 0.9, h: 0.9, fill: { color: i === 2 ? HEX.coral : HEX.mint }, line: { type: "none" }, objectName: `a${2 + i}_dot` });
  s.addImage({ path: ic(icn, i === 2 ? "white" : "navy"), x: 0.84, y: y + 0.24, w: 0.42, h: 0.42, objectName: `a${2 + i}_icon`, altText: h });
  T(s, h, { x: 1.85, y: y - 0.02, w: 6, h: 0.5, fontSize: 22, bold: true, color: "FFFFFF", objectName: `a${2 + i}_h` });
  T(s, d, { x: 1.85, y: y + 0.45, w: 6.2, h: 0.6, fontSize: 16, color: HEX.mutedDark, objectName: `a${2 + i}_d` });
});
s.addNotes("Finally, our goals. In six months, we want to build an active community around NutriPill. In twelve months, we want to grow our digital reach and double our customer base. In the long term, we want to become a leader in the local market and expand nationwide.");

// ================= 10. THANK YOU =================
pres.addSection({ title: "Close" });
s = pres.addSlide({ masterName: "COVER", sectionTitle: "Close" });
s.addImage({ path: A("hero.png"), x: 3.67, y: -0.2, w: 6.0, h: 6.0, objectName: "a1_hero", altText: "NutriPill capsule illustration" });
T(s, "Thank you!", { x: 1.5, y: 4.55, w: 10.33, h: 1.1, fontSize: 60, bold: true, fontFace: THEME.headFontFace, color: "FFFFFF", align: "center", objectName: "a2_title" });
T(s, "Any questions?", { x: 1.5, y: 5.6, w: 10.33, h: 0.55, fontSize: 24, color: HEX.mint, italic: true, align: "center", objectName: "a3_q" });
s.addImage({ path: A("logo-light.png"), x: 5.79, y: 6.45, w: 1.76, h: 0.49, objectName: "a4_logo", altText: "NutriPill logo" });
s.addNotes("Thank you for listening! NutriPill: essential nutrients, anytime, anywhere. Do you have any questions?");

(async () => {
  const out = path.join(__dirname, "NutriPill.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("wrote", out);
})();
