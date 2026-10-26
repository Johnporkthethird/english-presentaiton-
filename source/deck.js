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
const T = (slide, text, opts) => slide.addText(text, { isTextBox: true, fontFace: THEME.bodyFontFace, margin: 0, valign: "top", ...opts });
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
T(s, "BUSINESS PROPOSAL", { x: 0.8, y: 2.15, w: 6.5, h: 0.35, fontSize: 13, bold: true, charSpacing: 4, color: HEX.mint, objectName: "a3_kicker" });
T(s, [{ text: "Nutri", options: { color: "FFFFFF" } }, { text: "Pill", options: { color: HEX.mint } }], { x: 0.75, y: 2.5, w: 6.5, h: 1.5, fontSize: 80, bold: true, fontFace: THEME.headFontFace, objectName: "a4_title" });
T(s, "Essential nutrients for busy lives", { x: 0.8, y: 4.0, w: 6.2, h: 0.55, fontSize: 24, color: "FFFFFF", italic: true, objectName: "a5_tag" });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.8, y: 5.25, w: 4.9, h: 0.6, rectRadius: 0.3, fill: { color: "FFFFFF", transparency: 88 }, line: { color: "FFFFFF", transparency: 70, width: 1 }, objectName: "a6_pill" });
T(s, "By Dani, Max, William & Miguel", { x: 0.8, y: 5.25, w: 4.9, h: 0.6, fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle", objectName: "a6_names" });
s.addNotes("Good morning, everyone. We are Dani, Max, William and Miguel, and today we would like to present our business proposal: NutriPill, a product that brings essential nutrients to people with busy lives. Over the next few minutes, we will explain the problem we have identified, our solution, who it is for, and how we plan to turn this idea into a successful brand.");

// ================= 2. INTRODUCTION =================
pres.addSection({ title: "The idea" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "The idea" });
s.addText("01 / 08", { placeholder: "kicker" });
s.addText("Introduction", { placeholder: "title" });
s.addImage({ path: A("hero-light.png"), x: 8.15, y: 2.05, w: 4.6, h: 4.6, objectName: "a1_art", altText: "Capsule illustration" });
T(s, "Have you ever been so busy that you simply didn't have time to eat?", { x: 0.6, y: 2.05, w: 7.0, h: 1.0, fontSize: 24, bold: true, color: HEX.navy, objectName: "a2_q" });
T(s, "Imagine a pill that could give your body the essential nutrients it needs on those days when there is no time for a proper meal.", { x: 0.6, y: 3.05, w: 7.0, h: 0.9, fontSize: 18, color: HEX.muted, objectName: "a2_text" });
card(s, 0.6, 4.2, 7.0, 2.5, "FFFFFF", "a3");
s.addImage({ path: A("logo-dark.png"), x: 0.95, y: 4.45, w: 2.16, h: 0.6, objectName: "a3_logo", altText: "NutriPill logo" });
T(s, "Meet NutriPill: a convenient way to get essential nutrients on the go. Small, simple, and designed to fit perfectly into your busy lifestyle.", { x: 0.95, y: 5.1, w: 6.35, h: 0.8, fontSize: 15, color: HEX.muted, objectName: "a3_text" });
[["Small", 0.95], ["Simple", 2.45], ["On the go", 3.95]].forEach(([t, x], i) => {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 6.0, w: 1.35, h: 0.45, rectRadius: 0.22, fill: { color: "E3FAF4" }, line: { type: "none" }, objectName: `a${4 + i}_chip` });
  T(s, t, { x, y: 6.0, w: 1.35, h: 0.45, fontSize: 14, bold: true, color: "0FA888", align: "center", valign: "middle", objectName: `a${4 + i}_chiptext` });
});
s.addNotes("Let's start with a simple question: have you ever been so busy that you simply didn't have time to eat? Most of us have experienced this at some point. Now, imagine a pill that could give your body the essential nutrients it needs on those days when there is no time for a proper meal. That is exactly what NutriPill is: a convenient way to get essential nutrients on the go. It is small, simple, and designed to fit perfectly into a busy lifestyle.");

// ================= 3. THE PROBLEM =================
s = pres.addSlide({ masterName: "DARK", sectionTitle: "The idea" });
s.addText("02 / 08", { placeholder: "kicker" });
s.addText("The Problem", { placeholder: "title" });
T(s, "Nowadays, many people have such busy schedules that they don't have enough time to prepare or eat proper meals. Students and workers, in particular, often skip meals because they are always in a hurry.", { x: 0.6, y: 1.95, w: 11.5, h: 1.05, fontSize: 18, color: HEX.mutedDark, objectName: "a1_text" });
const probs = [
  ["battery", "Low energy", "Without regular meals, the body runs out of fuel long before the day is over."],
  ["brain", "Difficulty concentrating", "Skipping meals makes it much harder to stay focused in class or at work."],
  ["apple", "Poor nutrition", "Over time, the body misses out on the nutrients it needs to stay healthy."],
];
probs.forEach(([icn, h, d], i) => {
  const x = 0.6 + i * 4.1;
  card(s, x, 3.25, 3.8, 2.55, "FFFFFF", `a${2 + i}`, { fill: { transparency: 92 }, line: { color: "FFFFFF", transparency: 80, width: 1 }, noShadow: true });
  iconCircle(s, icn, x + 0.35, 3.5, 0.8, HEX.coral, "white", `a${2 + i}`);
  T(s, h, { x: x + 0.35, y: 4.45, w: 3.2, h: 0.45, fontSize: 19, bold: true, color: "FFFFFF", objectName: `a${2 + i}_h` });
  T(s, d, { x: x + 0.35, y: 4.9, w: 3.15, h: 0.8, fontSize: 14, color: HEX.mutedDark, objectName: `a${2 + i}_d` });
});
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 6.05, w: 12.0, h: 0.65, rectRadius: 0.32, fill: { color: HEX.mint }, line: { type: "none" }, objectName: "a5_bar" });
T(s, "What they need is a quick and convenient way to get essential nutrients when there is no time to eat.", { x: 0.6, y: 6.05, w: 12.0, h: 0.65, fontSize: 17, bold: true, color: HEX.navy, align: "center", valign: "middle", objectName: "a5_bartext" });
s.addNotes("So, what is the problem? Nowadays, many people have such busy schedules that they don't have enough time to prepare or eat proper meals. Students and workers, in particular, often skip meals because they are always in a hurry. As a result, they suffer from low energy, they find it difficult to concentrate, and, over time, their nutrition becomes poor. Clearly, what these people need is a quick and convenient way to get essential nutrients when there is simply no time to eat.");

// ================= 4. OUR SOLUTION =================
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "The idea" });
s.addText("03 / 08", { placeholder: "kicker" });
s.addText("Our Solution", { placeholder: "title" });
s.addImage({ path: A("hero-light.png"), x: 0.45, y: 2.0, w: 4.4, h: 4.4, objectName: "a1_art", altText: "Capsule illustration" });
const feats = [
  ["lightbulb", "Innovative", "A brand-new way of getting essential nutrients in seconds."],
  ["suitcase", "Small and easy to carry", "It fits easily into a pocket, backpack or bag."],
  ["bolt", "Keeps your energy up", "It helps you maintain your energy throughout the day."],
  ["heart", "Perfect for busy people", "Ideal for students and workers with demanding schedules."],
];
feats.forEach(([icn, h, d], i) => {
  const x = 5.3 + (i % 2) * 3.8, y = 2.05 + Math.floor(i / 2) * 1.85;
  card(s, x, y, 3.5, 1.6, "FFFFFF", `a${2 + i}`);
  iconCircle(s, icn, x + 0.25, y + 0.3, 0.7, "E3FAF4", "mint", `a${2 + i}`);
  T(s, h, { x: x + 1.15, y: y + 0.2, w: 2.25, h: 0.45, fontSize: 15, bold: true, color: HEX.navy, objectName: `a${2 + i}_h` });
  T(s, d, { x: x + 1.15, y: y + 0.65, w: 2.2, h: 0.8, fontSize: 14, color: HEX.muted, objectName: `a${2 + i}_d` });
});
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.3, y: 5.85, w: 7.3, h: 0.85, rectRadius: 0.15, fill: { color: "FFF0EC" }, line: { type: "none" }, objectName: "a6_note" });
T(s, [{ text: "Please note: ", options: { bold: true, color: HEX.coral } }, { text: "although NutriPill does not replace a complete meal, it offers a practical way to supplement your nutrition when life gets busy.", options: { color: HEX.navy } }],
  { x: 5.55, y: 5.85, w: 6.9, h: 0.85, fontSize: 14, valign: "middle", objectName: "a6_notetext" });
s.addNotes("This is where our solution comes in. NutriPill is an innovative and convenient pill designed to provide essential nutrients when people don't have time to eat. It is small, easy to carry, and perfect for busy students and workers. Our main goal is to help people maintain their energy and get extra nutrients throughout the day. However, we want to be honest: NutriPill does not replace a complete meal. Instead, it offers a practical way to supplement your nutrition when life gets busy.");

// ================= 5. TARGET AUDIENCE =================
s = pres.addSlide({ masterName: "DARK", sectionTitle: "The idea" });
s.addText("04 / 08", { placeholder: "kicker" });
s.addText("Who Is Our Brand Directed To?", { placeholder: "title" });
T(s, "NutriPill is designed for busy people who don't always have time to eat properly, especially those who need a quick and convenient way to supplement their nutrition during a hectic day.", { x: 0.6, y: 1.95, w: 11.5, h: 0.85, fontSize: 18, color: HEX.mutedDark, objectName: "a1_text" });
const aud = [
  ["grad", "Students", "Long days of classes, exams and homework often leave little time for lunch."],
  ["briefcase", "Workers", "Tight deadlines and back-to-back meetings mean meals are often skipped."],
  ["run", "Athletes", "Intense training requires a steady supply of essential nutrients."],
  ["clock", "Hectic lifestyles", "Anyone who is constantly on the move and short on time."],
];
aud.forEach(([icn, h, d], i) => {
  const x = 0.6 + i * 3.08;
  card(s, x, 3.05, 2.8, 3.65, "FFFFFF", `a${2 + i}`);
  iconCircle(s, icn, x + 0.85, 3.35, 1.1, HEX.mint, "white", `a${2 + i}`);
  T(s, h, { x: x + 0.2, y: 4.65, w: 2.4, h: 0.5, fontSize: 19, bold: true, color: HEX.navy, align: "center", objectName: `a${2 + i}_h` });
  T(s, d, { x: x + 0.22, y: 5.15, w: 2.36, h: 1.3, fontSize: 14, color: HEX.muted, align: "center", objectName: `a${2 + i}_d` });
});
s.addNotes("But who exactly is our brand directed to? NutriPill is designed for busy people who don't always have time to eat properly. Our main target audience includes students, who spend long days in class and studying; workers, who often skip lunch because of tight deadlines and meetings; athletes, who need a steady supply of nutrients for their training; and, in general, anyone with a hectic lifestyle. It is especially useful for those who need a quick and convenient way to supplement their nutrition during a busy day.");

// ================= 6. ACTION PLAN =================
pres.addSection({ title: "The business" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "The business" });
s.addText("05 / 08", { placeholder: "kicker" });
s.addText("Action Plan", { placeholder: "title" });
T(s, "Our business model is built on three key pillars:", { x: 0.6, y: 1.85, w: 11, h: 0.45, fontSize: 18, color: HEX.muted, objectName: "a1_sub" });
const pillars = [
  ["coins", "Revenue", "We will generate income through direct sales of NutriPill, as well as experiences linked to the product."],
  ["share", "Channels", "We will build a strong presence on the main social networks, combined with face-to-face experiences."],
  ["tag", "Pricing", "Our prices will be affordable but with added value: a premium option that remains accessible to everyone."],
];
pillars.forEach(([icn, h, d], i) => {
  const x = 0.6 + i * 4.1;
  card(s, x, 2.5, 3.8, 4.2, "FFFFFF", `a${2 + i}`);
  T(s, `0${i + 1}`, { x: x + 2.4, y: 2.7, w: 1.2, h: 0.8, fontSize: 40, fontFace: THEME.headFontFace, color: "C8F0E5", align: "right", objectName: `a${2 + i}_num` });
  iconCircle(s, icn, x + 0.4, 2.8, 1.0, HEX.navy, "mint", `a${2 + i}`);
  T(s, h, { x: x + 0.4, y: 4.0, w: 3.0, h: 0.55, fontSize: 24, bold: true, color: HEX.navy, objectName: `a${2 + i}_h` });
  T(s, d, { x: x + 0.4, y: 4.55, w: 3.05, h: 1.35, fontSize: 16, color: HEX.muted, objectName: `a${2 + i}_d` });
});
["instagram", "tiktok", "youtube"].forEach((n, j) => {
  s.addImage({ path: ic(n, "navy"), x: 5.1 + j * 0.65, y: 6.0, w: 0.42, h: 0.42, objectName: "a3_social", altText: n });
});
s.addNotes("Now let's move on to our action plan. Our business model is built on three key pillars. Firstly, revenue: we will generate income through direct sales of NutriPill, as well as through experiences linked to the product. Secondly, channels: we will build a strong presence on the main social networks, combined with face-to-face experiences, so that people can get to know the brand in person. Finally, pricing: our prices will be affordable but with added value. In other words, NutriPill will be a premium option that remains accessible to everyone.");

// ================= 7. GROWTH STRATEGY =================
s = pres.addSlide({ masterName: "DARK", sectionTitle: "The business" });
s.addText("06 / 08", { placeholder: "kicker" });
s.addText("Growth Strategy", { placeholder: "title" });
s.addShape(pres.shapes.LINE, { x: 1.2, y: 2.85, w: 10.9, h: 0, line: { color: HEX.mint, width: 2, dashType: "dash" }, objectName: "a1_line" });
const steps = [
  ["camera", "Create inspiring content", "We will share content on social media that shows a real, everyday lifestyle."],
  ["star", "Work with local influencers", "We will partner with influencers who truly represent our brand's philosophy."],
  ["gift", "Create memorable experiences", "We will organise events, offer personalised kits and develop collaborations."],
  ["users", "Actively build a community", "We will invite our customers to become a real part of the brand."],
];
steps.forEach(([icn, h, d], i) => {
  const x = 0.6 + i * 3.1, cx = x + 0.6;
  s.addShape(pres.shapes.OVAL, { x: cx - 0.55, y: 2.3, w: 1.1, h: 1.1, fill: { color: HEX.navy }, line: { color: HEX.mint, width: 3 }, objectName: `a${2 + i}_ring` });
  s.addImage({ path: ic(icn, "mint"), x: cx - 0.27, y: 2.58, w: 0.54, h: 0.54, objectName: `a${2 + i}_icon`, altText: h });
  T(s, `0${i + 1}`, { x, y: 3.7, w: 2.8, h: 0.5, fontSize: 22, fontFace: THEME.headFontFace, color: HEX.coral, objectName: `a${2 + i}_num` });
  T(s, h, { x, y: 4.2, w: 2.85, h: 0.85, fontSize: 19, bold: true, color: "FFFFFF", objectName: `a${2 + i}_h` });
  T(s, d, { x, y: 5.1, w: 2.8, h: 1.3, fontSize: 15, color: HEX.mutedDark, objectName: `a${2 + i}_d` });
});
s.addNotes("Of course, having a good product is not enough; we also need a clear growth strategy. It consists of four steps. First of all, we will create inspiring content on social media that shows a real, everyday lifestyle. Next, we will work with local influencers who truly represent our brand's philosophy. After that, we will create memorable experiences, such as events, personalised kits and collaborations. Last but not least, we will actively build a community by inviting our customers to become a real part of the brand.");

// ================= 8. OUR PROPOSAL =================
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "The business" });
s.addText("07 / 08", { placeholder: "kicker" });
s.addText("Our Proposal", { placeholder: "title" });
iconCircle(s, "handshake", 0.6, 2.1, 1.2, HEX.mint, "white", "a1");
T(s, "We are looking for brands that want to grow with us.", { x: 0.6, y: 3.55, w: 5.6, h: 0.9, fontSize: 22, bold: true, color: HEX.navy, objectName: "a2_lead" });
T(s, "What we propose is a strategic partnership in which you gain visibility, a stronger position among young consumers and a connection with new audiences.", { x: 0.6, y: 4.5, w: 5.6, h: 1.4, fontSize: 18, color: HEX.muted, objectName: "a2_text" });
card(s, 6.75, 2.1, 5.85, 4.6, HEX.navy, "a3");
T(s, "WITH YOUR SUPPORT, WE CAN:", { x: 7.2, y: 2.45, w: 5, h: 0.4, fontSize: 14, bold: true, charSpacing: 3, color: HEX.mint, objectName: "a3_h" });
["Develop joint products and experiences", "Increase our reach through campaigns", "Generate greater credibility and growth"].forEach((t, i) => {
  const y = 3.15 + i * 1.1;
  s.addShape(pres.shapes.OVAL, { x: 7.2, y, w: 0.6, h: 0.6, fill: { color: HEX.mint }, line: { type: "none" }, objectName: `a${4 + i}_dot` });
  s.addImage({ path: ic("check", "navy"), x: 7.35, y: y + 0.15, w: 0.3, h: 0.3, objectName: `a${4 + i}_check`, altText: "check" });
  T(s, t, { x: 8.05, y: y - 0.1, w: 4.3, h: 0.8, fontSize: 18, color: "FFFFFF", valign: "middle", objectName: `a${4 + i}_t` });
});
s.addNotes("This brings us to our proposal. We are looking for brands that want to grow with us. What we propose is a strategic partnership in which our partners gain visibility, a stronger position among young consumers, and a connection with new audiences. With your support, we can develop joint products and experiences, increase our reach through advertising campaigns, and generate greater credibility and growth for both of us.");

// ================= 9. GOALS =================
s = pres.addSlide({ masterName: "DARK", sectionTitle: "The business" });
s.addText("08 / 08", { placeholder: "kicker" });
s.addText("What We Expect to Achieve", { placeholder: "title" });
s.addImage({ path: A("hero.png"), x: 8.3, y: 2.0, w: 4.8, h: 4.8, objectName: "a1_art", altText: "Capsule illustration" });
s.addShape(pres.shapes.LINE, { x: 1.05, y: 2.6, w: 0, h: 3.6, line: { color: HEX.mint, width: 2, dashType: "dash" }, objectName: "a1_line" });
const goals = [
  ["flag", "In 6 months", "Consolidate an active community around our brand."],
  ["chart", "In 12 months", "Increase our digital reach and double our customer base."],
  ["trophy", "In the long term", "Establish ourselves as a leading brand in the local market, with expansion at a national level."],
];
goals.forEach(([icn, h, d], i) => {
  const y = 2.2 + i * 1.6;
  s.addShape(pres.shapes.OVAL, { x: 0.6, y, w: 0.9, h: 0.9, fill: { color: i === 2 ? HEX.coral : HEX.mint }, line: { type: "none" }, objectName: `a${2 + i}_dot` });
  s.addImage({ path: ic(icn, i === 2 ? "white" : "navy"), x: 0.84, y: y + 0.24, w: 0.42, h: 0.42, objectName: `a${2 + i}_icon`, altText: h });
  T(s, h, { x: 1.85, y: y - 0.05, w: 6, h: 0.5, fontSize: 22, bold: true, color: "FFFFFF", objectName: `a${2 + i}_h` });
  T(s, d, { x: 1.85, y: y + 0.42, w: 6.2, h: 0.8, fontSize: 16, color: HEX.mutedDark, objectName: `a${2 + i}_d` });
});
s.addNotes("Finally, we would like to share what we expect to achieve. In six months, we aim to consolidate an active community around our brand. In twelve months, we hope to increase our digital reach and double our customer base. And in the long term, our goal is to establish ourselves as a leading brand in the local market, with expansion at a national level. To sum up, NutriPill is a simple solution to a very common problem. Thank you very much for your attention. Do you have any questions?");

(async () => {
  const out = path.join(__dirname, "NutriPill.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("wrote", out);
})();
