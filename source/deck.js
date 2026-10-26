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
T(s, [{ text: "\u201CJust lock in: 1 pill a day keeps the hunger away!\u201D", options: {} }], { x: 0.8, y: 4.0, w: 5.9, h: 0.95, fontSize: 22, color: "FFFFFF", italic: true, objectName: "a5_tag" });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.8, y: 5.45, w: 4.9, h: 0.6, rectRadius: 0.3, fill: { color: "FFFFFF", transparency: 88 }, line: { color: "FFFFFF", transparency: 70, width: 1 }, objectName: "a6_pill" });
T(s, "By Dani, Max, William & Miguel", { x: 0.8, y: 5.45, w: 4.9, h: 0.6, fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle", objectName: "a6_names" });
s.addNotes("Hi everyone. We're Dani, Max, William and Miguel, and today we're going to present our business idea: NutriPill. Our slogan is: Just lock in: 1 pill a day keeps the hunger away! The idea came from our own experience. As students, we often have days that are so busy that we don't have time to eat properly, so we asked ourselves: what if there was a simple way to get the nutrients you need on those days?");

// ================= 2. INTRODUCTION =================
pres.addSection({ title: "The idea" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "The idea" });
s.addText("01 / 13", { placeholder: "kicker" });
s.addText("Introduction", { placeholder: "title" });
s.addImage({ path: A("hero-light.png"), x: 8.15, y: 2.05, w: 4.6, h: 4.6, objectName: "a1_art", altText: "Capsule illustration" });
T(s, "Have you ever been too busy to eat?", { x: 0.6, y: 2.05, w: 7.0, h: 0.6, fontSize: 24, bold: true, color: HEX.navy, objectName: "a2_q" });
T(s, "Think about a day with classes in the morning, training in the afternoon and homework at night. Sometimes, lunch just doesn't happen.", { x: 0.6, y: 2.8, w: 7.0, h: 1.2, fontSize: 18, color: HEX.muted, objectName: "a2_text" });
card(s, 0.6, 4.2, 7.0, 2.5, "FFFFFF", "a3");
s.addImage({ path: A("logo-dark.png"), x: 0.95, y: 4.45, w: 2.16, h: 0.6, objectName: "a3_logo", altText: "NutriPill logo" });
T(s, "That's why we came up with NutriPill: one small pill with the nutrients your body needs, for the days when you can't sit down for a proper meal.", { x: 0.95, y: 5.1, w: 6.35, h: 0.8, fontSize: 15, color: HEX.muted, objectName: "a3_text" });
[["Small", 0.95], ["Simple", 2.45], ["On the go", 3.95]].forEach(([t, x], i) => {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 6.0, w: 1.35, h: 0.45, rectRadius: 0.22, fill: { color: "E3FAF4" }, line: { type: "none" }, objectName: `a${4 + i}_chip` });
  T(s, t, { x, y: 6.0, w: 1.35, h: 0.45, fontSize: 14, bold: true, color: "0FA888", align: "center", valign: "middle", objectName: `a${4 + i}_chiptext` });
});
s.addNotes("So, let me start with a question: have you ever been too busy to eat? Think about a normal day for a lot of us: classes in the morning, training or work in the afternoon, and homework at night. On days like that, lunch is often the first thing we skip. That's why we came up with NutriPill. It's one small pill with the nutrients your body needs, for the days when you can't sit down for a proper meal.");

// ================= 3. THE PROBLEM =================
s = pres.addSlide({ masterName: "DARK", sectionTitle: "The idea" });
s.addText("02 / 13", { placeholder: "kicker" });
s.addText("The Problem", { placeholder: "title" });
T(s, "A lot of people don't have time to cook, or even to sit down and eat. Students rush from one class to the next, and many workers eat at their desk, or don't eat at all.", { x: 0.6, y: 1.95, w: 11.5, h: 1.05, fontSize: 18, color: HEX.mutedDark, objectName: "a1_text" });
const probs = [
  ["battery", "Low energy", "By the afternoon you feel tired and slow, even if you slept well."],
  ["brain", "Hard to concentrate", "It's really difficult to pay attention in class or at work when you're hungry."],
  ["apple", "Poor nutrition", "When people do eat in a hurry, it's usually crisps, sweets or fast food."],
];
probs.forEach(([icn, h, d], i) => {
  const x = 0.6 + i * 4.1;
  card(s, x, 3.25, 3.8, 2.55, "FFFFFF", `a${2 + i}`, { fill: { transparency: 92 }, line: { color: "FFFFFF", transparency: 80, width: 1 }, noShadow: true });
  iconCircle(s, icn, x + 0.35, 3.5, 0.8, HEX.coral, "white", `a${2 + i}`);
  T(s, h, { x: x + 0.35, y: 4.45, w: 3.2, h: 0.45, fontSize: 19, bold: true, color: "FFFFFF", objectName: `a${2 + i}_h` });
  T(s, d, { x: x + 0.35, y: 4.9, w: 3.15, h: 0.8, fontSize: 14, color: HEX.mutedDark, objectName: `a${2 + i}_d` });
});
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 6.05, w: 12.0, h: 0.65, rectRadius: 0.32, fill: { color: HEX.mint }, line: { type: "none" }, objectName: "a5_bar" });
T(s, "They need something quick and easy that still gives their body what it needs.", { x: 0.6, y: 6.05, w: 12.0, h: 0.65, fontSize: 17, bold: true, color: HEX.navy, align: "center", valign: "middle", objectName: "a5_bartext" });
s.addNotes("Now let's talk about the problem. These days, a lot of people simply don't have time to cook, or even to sit down and eat. Students go from one class to the next, and many workers eat at their desk or don't eat at all. And this has consequences. By the afternoon, you feel tired and slow. It's hard to concentrate in class or at work when you're hungry. And when people do eat in a hurry, they usually choose crisps, sweets or fast food, so their nutrition is poor. What these people need is something quick and easy that still gives their body what it needs.");

// ================= 4. OUR SOLUTION =================
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "The idea" });
s.addText("03 / 13", { placeholder: "kicker" });
s.addText("Our Solution", { placeholder: "title" });
s.addImage({ path: A("hero-light.png"), x: 0.45, y: 2.0, w: 4.4, h: 4.4, objectName: "a1_art", altText: "Capsule illustration" });
const feats = [
  ["lightbulb", "Quick to take", "Just take it with a glass of water and you're done."],
  ["suitcase", "Fits in your pocket", "Carry it in your backpack, gym bag or jacket."],
  ["bolt", "Keeps you going", "Extra nutrients to keep you active until your next meal."],
  ["heart", "Made for busy days", "For exam weeks, long shifts or non-stop days."],
];
feats.forEach(([icn, h, d], i) => {
  const x = 5.3 + (i % 2) * 3.8, y = 2.05 + Math.floor(i / 2) * 1.85;
  card(s, x, y, 3.5, 1.6, "FFFFFF", `a${2 + i}`);
  iconCircle(s, icn, x + 0.25, y + 0.3, 0.7, "E3FAF4", "mint", `a${2 + i}`);
  T(s, h, { x: x + 1.15, y: y + 0.2, w: 2.25, h: 0.45, fontSize: 15, bold: true, color: HEX.navy, objectName: `a${2 + i}_h` });
  T(s, d, { x: x + 1.15, y: y + 0.65, w: 2.2, h: 0.8, fontSize: 14, color: HEX.muted, objectName: `a${2 + i}_d` });
});
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.3, y: 5.85, w: 7.3, h: 0.85, rectRadius: 0.15, fill: { color: "FFF0EC" }, line: { type: "none" }, objectName: "a6_note" });
T(s, [{ text: "To be clear: ", options: { bold: true, color: HEX.coral } }, { text: "NutriPill doesn't replace a real meal. It's there for the days when a proper meal just isn't possible.", options: { color: HEX.navy } }],
  { x: 5.55, y: 5.85, w: 6.9, h: 0.85, fontSize: 14, valign: "middle", objectName: "a6_notetext" });
s.addNotes("This is where NutriPill comes in. It's quick to take: you just need a glass of water. It's small, so you can carry it in your backpack, your gym bag or even your jacket. It gives you extra nutrients to help you stay active until your next meal, and it's made for those really busy days, like exam weeks or long shifts at work. But we want to be honest about one thing: NutriPill doesn't replace a real meal. It's there to help on the days when a proper meal just isn't possible.");

// ================= BEST SELLER =================
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "The idea" });
s.addText("04 / 13", { placeholder: "kicker" });
s.addText("Our Best Seller", { placeholder: "title" });
s.addImage({ path: A("product.png"), x: 0.3, y: 1.75, w: 5.4, h: 5.4, objectName: "a1_product", altText: "NutriPill Daily jar with 30 capsules" });
// price badge
s.addShape(pres.shapes.OVAL, { x: 4.35, y: 1.95, w: 1.65, h: 1.65, fill: { color: HEX.coral }, line: { color: "FFFFFF", width: 4 }, shadow: shadow(), objectName: "a2_badge" });
T(s, [{ text: "€9.99", options: { bold: true, fontSize: 24, breakLine: true } }, { text: "30 days", options: { fontSize: 13 } }], { x: 4.35, y: 1.95, w: 1.65, h: 1.65, color: "FFFFFF", align: "center", valign: "middle", objectName: "a2_price" });
T(s, "NutriPill Daily", { x: 6.2, y: 2.0, w: 6.4, h: 0.6, fontSize: 28, bold: true, color: HEX.navy, objectName: "a3_name" });
T(s, "A jar of 30 capsules: one a day for a whole month. That's about 33 cents a day, less than a coffee.", { x: 6.2, y: 2.6, w: 6.4, h: 0.75, fontSize: 16, color: HEX.muted, objectName: "a3_sub" });
const best = [
  ["bolt", "Key feature", "Each capsule has the vitamins and minerals your body needs to keep going until your next meal."],
  ["thumbsup", "Why buy it?", "You stay focused and full of energy, even on days when you have no time to eat."],
  ["users", "Target buyer", "Students, workers and athletes aged 16 to 35 with busy schedules."],
];
best.forEach(([icn, h, d], i) => {
  const y = 3.55 + i * 1.12;
  card(s, 6.2, y, 6.4, 0.98, "FFFFFF", `a${4 + i}`);
  iconCircle(s, icn, 6.4, y + 0.19, 0.6, "E3FAF4", "mint", `a${4 + i}`);
  T(s, h, { x: 7.15, y: y + 0.1, w: 1.45, h: 0.78, fontSize: 16, bold: true, color: HEX.navy, valign: "middle", objectName: `a${4 + i}_h` });
  T(s, d, { x: 8.6, y: y + 0.06, w: 3.85, h: 0.86, fontSize: 14, color: HEX.muted, valign: "middle", objectName: `a${4 + i}_d` });
});
s.addNotes("This is our best seller: NutriPill Daily. It's a jar of 30 capsules, so you take one a day for a whole month, just like our slogan says. It costs 9 euros 99, which is about 33 cents a day, less than a coffee. The key feature is that each capsule has the vitamins and minerals your body needs to keep going until your next meal. So why should you buy it? Because you stay focused and full of energy, even on days when you have no time to eat. Our target buyers are students, workers and athletes between 16 and 35 who have busy schedules.");

// ================= 5. TARGET AUDIENCE =================
s = pres.addSlide({ masterName: "DARK", sectionTitle: "The idea" });
s.addText("05 / 13", { placeholder: "kicker" });
s.addText("Who Is Our Brand Directed To?", { placeholder: "title" });
T(s, "We're thinking about people who want to eat well but often can't find the time, people a lot like us.", { x: 0.6, y: 1.95, w: 11.5, h: 0.85, fontSize: 18, color: HEX.mutedDark, objectName: "a1_text" });
const aud = [
  ["grad", "Students", "Early classes, exams and homework. Lunch is often the first thing we skip."],
  ["briefcase", "Workers", "People who work long hours and skip lunch to get everything done."],
  ["run", "Athletes", "They train hard and need extra nutrients to recover and perform well."],
  ["clock", "Hectic lifestyles", "Parents, commuters, anyone whose day never seems to stop."],
];
aud.forEach(([icn, h, d], i) => {
  const x = 0.6 + i * 3.08;
  card(s, x, 3.05, 2.8, 3.65, "FFFFFF", `a${2 + i}`);
  iconCircle(s, icn, x + 0.85, 3.35, 1.1, HEX.mint, "white", `a${2 + i}`);
  T(s, h, { x: x + 0.2, y: 4.65, w: 2.4, h: 0.5, fontSize: 19, bold: true, color: HEX.navy, align: "center", objectName: `a${2 + i}_h` });
  T(s, d, { x: x + 0.22, y: 5.15, w: 2.36, h: 1.3, fontSize: 14, color: HEX.muted, align: "center", objectName: `a${2 + i}_d` });
});
s.addNotes("So, who is NutriPill for? Basically, people who want to eat well but often can't find the time, people a lot like us. First, students, because with early classes, exams and homework, lunch is usually the first thing we skip. Second, workers who do long hours and skip lunch to get everything done. Third, athletes, who train hard and need extra nutrients to recover. And finally, anyone with a hectic lifestyle, like parents or people who spend hours commuting.");

// ================= CORE VALUES =================
pres.addSection({ title: "Our company" });
s = pres.addSlide({ masterName: "DARK", sectionTitle: "Our company" });
s.addText("06 / 13", { placeholder: "kicker" });
s.addText("Our Core Values", { placeholder: "title" });
T(s, "Three ideas that guide every decision we make.", { x: 0.6, y: 1.85, w: 9, h: 0.5, fontSize: 18, color: HEX.mutedDark, objectName: "a1_sub" });
const vals = [
  ["rocket", "Innovation", "We want to change the way people eat on busy days, with an idea nobody else is offering.", HEX.mint, "navy"],
  ["leaf", "Eco-friendly", "We care about the planet as much as our customers' health, from ingredients to packaging.", "2E9E5B", "white"],
  ["handheart", "Accessibility", "Good nutrition shouldn't be a luxury. Everyone should be able to afford NutriPill.", HEX.coral, "white"],
];
vals.forEach(([icn, h, d, col, icol], i) => {
  const cx = 2.35 + i * 4.3;
  s.addShape(pres.shapes.OVAL, { x: cx - 1.25, y: 2.65, w: 2.5, h: 2.5, fill: { color: col, transparency: 85 }, line: { color: col, width: 2, dashType: "dash" }, objectName: `a${2 + i}_halo` });
  s.addShape(pres.shapes.OVAL, { x: cx - 0.9, y: 3.0, w: 1.8, h: 1.8, fill: { color: col }, line: { type: "none" }, shadow: { type: "outer", color: "000000", blur: 20, offset: 8, angle: 90, opacity: 0.35 }, objectName: `a${2 + i}_disc` });
  s.addImage({ path: ic(icn, icol), x: cx - 0.45, y: 3.45, w: 0.9, h: 0.9, objectName: `a${2 + i}_icon`, altText: h });
  T(s, h, { x: cx - 1.9, y: 5.3, w: 3.8, h: 0.55, fontSize: 24, bold: true, color: "FFFFFF", align: "center", objectName: `a${2 + i}_h` });
  T(s, d, { x: cx - 1.8, y: 5.85, w: 3.6, h: 0.9, fontSize: 14, color: HEX.mutedDark, align: "center", objectName: `a${2 + i}_d` });
});
s.addNotes("Every company needs clear values, and ours are three. The first one is innovation: we want to change the way people eat on busy days, with an idea that nobody else is really offering. The second one is being eco-friendly: we care about the planet as much as our customers' health, from the ingredients we use to the packaging. And the third one is accessibility: we believe good nutrition shouldn't be a luxury, so everyone should be able to afford NutriPill.");

// ================= ENVIRONMENTAL POLICY =================
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Our company" });
s.addText("07 / 13", { placeholder: "kicker" });
s.addText("Environmental Policy", { placeholder: "title" });
s.addImage({ path: A("eco.png"), x: 8.1, y: 1.95, w: 4.7, h: 4.7, objectName: "a1_art", altText: "Leaf and capsule illustration" });
T(s, "We don't want to help people by hurting the planet.", { x: 0.6, y: 1.95, w: 7.2, h: 0.5, fontSize: 20, bold: true, color: "2E9E5B", objectName: "a2_lead" });
const eco = [
  ["seedling", "Natural ingredients", "Our capsules only contain natural ingredients, taken from plants and fruit."],
  ["solar", "Renewable farms", "We buy from plant and fruit farms that use renewable energy, like solar power."],
  ["recycle", "Recyclable packaging", "Our jars are made from recycled plastic and can be recycled again."],
];
eco.forEach(([icn, h, d], i) => {
  const y = 2.75 + i * 1.3;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 7.2, h: 1.1, rectRadius: 0.55, fill: { color: "E4F7EA" }, line: { type: "none" }, objectName: `a${3 + i}_row` });
  s.addShape(pres.shapes.OVAL, { x: 0.75, y: y + 0.15, w: 0.8, h: 0.8, fill: { color: "2E9E5B" }, line: { type: "none" }, objectName: `a${3 + i}_dot` });
  s.addImage({ path: ic(icn, "white"), x: 0.95, y: y + 0.35, w: 0.4, h: 0.4, objectName: `a${3 + i}_icon`, altText: h });
  T(s, h, { x: 1.8, y: y + 0.12, w: 5.8, h: 0.4, fontSize: 18, bold: true, color: HEX.navy, objectName: `a${3 + i}_h` });
  T(s, d, { x: 1.8, y: y + 0.52, w: 5.8, h: 0.5, fontSize: 14, color: HEX.muted, objectName: `a${3 + i}_d` });
});
s.addNotes("Being eco-friendly is one of our values, so we have a clear environmental policy. Basically, we don't want to help people by hurting the planet. First, our capsules only contain natural ingredients, taken from plants and fruit. Second, we buy these ingredients from farms that use renewable energy, like solar power. And finally, our jars are made from recycled plastic, and they can be recycled again once they're empty.");

// ================= WORKPLACE ETHICS =================
s = pres.addSlide({ masterName: "DARK", sectionTitle: "Our company" });
s.addText("08 / 13", { placeholder: "kicker" });
s.addText("Workplace Ethics & Social Responsibility", { placeholder: "title" });
card(s, 0.6, 2.05, 6.0, 4.65, HEX.mint, "a1", { noShadow: true });
s.addImage({ path: ic("quote", "navy"), x: 1.0, y: 2.45, w: 0.7, h: 0.7, objectName: "a1_quote", altText: "quote" });
T(s, "Everyone at NutriPill treats each other with respect, no matter their gender or race.", { x: 1.0, y: 3.35, w: 5.2, h: 2.1, fontSize: 28, bold: true, color: HEX.navy, objectName: "a2_quote" });
T(s, "This is the first rule of our company.", { x: 1.0, y: 5.7, w: 5.2, h: 0.5, fontSize: 16, italic: true, color: HEX.navy, objectName: "a2_cap" });
const eth = [
  ["balance", "Equal treatment", "Every employee has the same opportunities, and discrimination is never accepted."],
  ["shield", "Shared values", "Our workers are expected to follow our core values: innovation, sustainability and accessibility."],
  ["euro", "Fair prices for everyone", "Our price is affordable, so people from all income groups can try NutriPill and lock in."],
];
eth.forEach(([icn, h, d], i) => {
  const y = 2.05 + i * 1.6;
  card(s, 6.95, y, 5.65, 1.4, "FFFFFF", `a${3 + i}`, { fill: { transparency: 92 }, line: { color: "FFFFFF", transparency: 80, width: 1 }, noShadow: true });
  iconCircle(s, icn, 7.2, y + 0.3, 0.8, HEX.coral, "white", `a${3 + i}`);
  T(s, h, { x: 8.25, y: y + 0.2, w: 4.2, h: 0.4, fontSize: 18, bold: true, color: "FFFFFF", objectName: `a${3 + i}_h` });
  T(s, d, { x: 8.25, y: y + 0.6, w: 4.2, h: 0.7, fontSize: 14, color: HEX.mutedDark, objectName: `a${3 + i}_d` });
});
s.addNotes("Now let's talk about how we work as a company. The first rule at NutriPill is that everyone treats each other with respect, no matter their gender or race. Every employee has the same opportunities, and discrimination is never accepted. We also expect our workers to follow our core values: innovation, sustainability and accessibility. And our social responsibility also includes our customers: our price is affordable, so people from all income groups can try NutriPill and, as our slogan says, lock in.");

// ================= 6. ACTION PLAN =================
pres.addSection({ title: "The business" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "The business" });
s.addText("09 / 13", { placeholder: "kicker" });
s.addText("Action Plan", { placeholder: "title" });
T(s, "How NutriPill will make money and reach people:", { x: 0.6, y: 1.85, w: 11, h: 0.45, fontSize: 18, color: HEX.muted, objectName: "a1_sub" });
const pillars = [
  ["coins", "Revenue", "We'll sell NutriPill directly, online and in person, and also earn money from events and pop-up stands."],
  ["share", "Channels", "Our customers are on Instagram and TikTok, so that's where we'll be. We'll also have stands at schools and gyms."],
  ["tag", "Pricing", "Cheap enough for a student to buy, but with the quality of a premium product."],
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
s.addNotes("Now, how are we actually going to make this work? Our plan has three parts. First, revenue: we'll make money by selling NutriPill directly, both online and in person, and also through events and pop-up stands. Second, channels: we know our customers spend a lot of time on Instagram and TikTok, so that's where we'll focus. But we also want people to try the product in real life, so we'll set up stands at schools and gyms. And third, pricing: we want NutriPill to be cheap enough for a student to buy, but with the quality of a premium product.");

// ================= 7. GROWTH STRATEGY =================
s = pres.addSlide({ masterName: "DARK", sectionTitle: "The business" });
s.addText("10 / 13", { placeholder: "kicker" });
s.addText("Growth Strategy", { placeholder: "title" });
s.addShape(pres.shapes.LINE, { x: 1.2, y: 2.85, w: 10.9, h: 0, line: { color: HEX.mint, width: 2, dashType: "dash" }, objectName: "a1_line" });
const steps = [
  ["camera", "Post real content", "Short videos of a normal busy day: early class, training, and NutriPill in between."],
  ["star", "Work with local influencers", "Local athletes and creators who actually live busy lives, not just anyone with followers."],
  ["gift", "Organise events", "Free sample days, personalised kits and collaborations with gyms and sports clubs."],
  ["users", "Listen to our customers", "Ask for their opinions, share their stories and let them help shape new products."],
];
steps.forEach(([icn, h, d], i) => {
  const x = 0.6 + i * 3.1, cx = x + 0.6;
  s.addShape(pres.shapes.OVAL, { x: cx - 0.55, y: 2.3, w: 1.1, h: 1.1, fill: { color: HEX.navy }, line: { color: HEX.mint, width: 3 }, objectName: `a${2 + i}_ring` });
  s.addImage({ path: ic(icn, "mint"), x: cx - 0.27, y: 2.58, w: 0.54, h: 0.54, objectName: `a${2 + i}_icon`, altText: h });
  T(s, `0${i + 1}`, { x, y: 3.7, w: 2.8, h: 0.5, fontSize: 22, fontFace: THEME.headFontFace, color: HEX.coral, objectName: `a${2 + i}_num` });
  T(s, h, { x, y: 4.2, w: 2.85, h: 0.85, fontSize: 19, bold: true, color: "FFFFFF", objectName: `a${2 + i}_h` });
  T(s, d, { x, y: 5.1, w: 2.8, h: 1.3, fontSize: 15, color: HEX.mutedDark, objectName: `a${2 + i}_d` });
});
s.addNotes("To grow the brand, we have four steps. First, we'll post real content: short videos of a normal busy day, showing early classes, training, and NutriPill in between. We don't want fake, perfect adverts. Second, we'll work with local influencers, but only athletes and creators who actually live busy lives, not just anyone with a lot of followers. Third, we'll organise events, like free sample days, and offer personalised kits and collaborations with gyms and sports clubs. And finally, we'll listen to our customers: we'll ask for their opinions, share their stories, and let them help us shape new products.");

// ================= SWOT =================
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "The business" });
s.addText("11 / 13", { placeholder: "kicker" });
s.addText("SWOT Analysis", { placeholder: "title" });
const swot = [
  ["S", "Strengths", "thumbsup", HEX.mint, ["Small, cheap and easy to carry", "Quick: one pill and you're done", "Natural ingredients"]],
  ["W", "Weaknesses", "warning", HEX.coral, ["It doesn't replace a real meal", "We're a new brand nobody knows yet", "Some people don't trust supplements"]],
  ["O", "Opportunities", "globe", "2A6BD1", ["More people have busy lives every year", "Healthy living is a big trend on social media", "Partnerships with gyms and supermarkets"]],
  ["T", "Threats", "shield", HEX.navy, ["Big supplement brands", "Energy drinks and protein bars", "Strict health rules for new products"]],
];
swot.forEach(([L, h, icn, col, items], i) => {
  const x = 0.6 + (i % 2) * 6.1, y = 1.95 + Math.floor(i / 2) * 2.45;
  card(s, x, y, 5.9, 2.25, "FFFFFF", `a${1 + i}`);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 1.5, h: 2.25, rectRadius: 0.18, fill: { color: col }, line: { type: "none" }, objectName: `a${1 + i}_side` });
  T(s, L, { x, y: y + 0.25, w: 1.5, h: 1.1, fontSize: 60, fontFace: THEME.headFontFace, bold: true, color: "FFFFFF", align: "center", valign: "middle", objectName: `a${1 + i}_L` });
  s.addImage({ path: ic(icn, "white"), x: x + 0.53, y: y + 1.45, w: 0.44, h: 0.44, objectName: `a${1 + i}_icon`, altText: h });
  T(s, h, { x: x + 1.8, y: y + 0.2, w: 3.9, h: 0.45, fontSize: 20, bold: true, color: col === HEX.navy ? HEX.navy : col, objectName: `a${1 + i}_h` });
  T(s, items.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < items.length - 1 } })), { x: x + 1.8, y: y + 0.7, w: 3.95, h: 1.4, fontSize: 15, color: HEX.navy, paraSpaceAfter: 4, objectName: `a${1 + i}_list` });
});
s.addNotes("Before going further, we did a SWOT analysis to look at NutriPill honestly. Our strengths are that it's small, cheap and easy to carry, it's very quick to take, and it uses natural ingredients. But we also have weaknesses: it doesn't replace a real meal, we're a new brand that nobody knows yet, and some people simply don't trust supplements. On the other hand, there are big opportunities: more people have busy lives every year, healthy living is a huge trend on social media, and we could partner with gyms and supermarkets. Finally, the main threats are big supplement brands, energy drinks and protein bars, and the strict health rules for new products.");

// ================= 8. OUR PROPOSAL =================
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "The business" });
s.addText("12 / 13", { placeholder: "kicker" });
s.addText("Our Proposal", { placeholder: "title" });
iconCircle(s, "handshake", 0.6, 2.1, 1.2, HEX.mint, "white", "a1");
T(s, "We are looking for brands that want to grow with us.", { x: 0.6, y: 3.55, w: 5.6, h: 0.9, fontSize: 22, bold: true, color: HEX.navy, objectName: "a2_lead" });
T(s, "For example, a gym, a sports brand or a healthy café. They help us reach more people, and in return they get noticed by young customers who are hard to reach.", { x: 0.6, y: 4.5, w: 5.6, h: 1.9, fontSize: 18, color: HEX.muted, objectName: "a2_text" });
card(s, 6.75, 2.1, 5.85, 4.6, HEX.navy, "a3");
T(s, "TOGETHER, WE COULD:", { x: 7.2, y: 2.45, w: 5, h: 0.4, fontSize: 14, bold: true, charSpacing: 3, color: HEX.mint, objectName: "a3_h" });
["Create joint products, like a gym pack with NutriPill", "Run campaigns together to reach more people", "Earn trust, because a partner people know makes us more believable"].forEach((t, i) => {
  const y = 3.15 + i * 1.1;
  s.addShape(pres.shapes.OVAL, { x: 7.2, y, w: 0.6, h: 0.6, fill: { color: HEX.mint }, line: { type: "none" }, objectName: `a${4 + i}_dot` });
  s.addImage({ path: ic("check", "navy"), x: 7.35, y: y + 0.15, w: 0.3, h: 0.3, objectName: `a${4 + i}_check`, altText: "check" });
  T(s, t, { x: 8.05, y: y - 0.1, w: 4.3, h: 0.8, fontSize: 18, color: "FFFFFF", valign: "middle", objectName: `a${4 + i}_t` });
});
s.addNotes("This brings us to our proposal. We're looking for brands that want to grow with us, for example a gym, a sports brand or a healthy caf\u00e9. The idea is simple: they help us reach more people, and in return they get noticed by young customers, who are usually hard to reach. Together, we could create joint products, like a gym pack that includes NutriPill. We could run campaigns together to reach more people. And we would both earn people's trust, because people believe in a new brand more when it's supported by a brand they already know.");

// ================= 9. GOALS =================
s = pres.addSlide({ masterName: "DARK", sectionTitle: "The business" });
s.addText("13 / 13", { placeholder: "kicker" });
s.addText("What We Expect to Achieve", { placeholder: "title" });
s.addImage({ path: A("hero.png"), x: 8.3, y: 2.0, w: 4.8, h: 4.8, objectName: "a1_art", altText: "Capsule illustration" });
s.addShape(pres.shapes.LINE, { x: 1.05, y: 2.6, w: 0, h: 3.6, line: { color: HEX.mint, width: 2, dashType: "dash" }, objectName: "a1_line" });
const goals = [
  ["flag", "In 6 months", "Have a group of loyal customers who use NutriPill and talk about it online."],
  ["chart", "In 12 months", "Reach more people online and double the number of customers we have."],
  ["trophy", "In the long term", "Become a well-known brand in our city first, and then grow across the whole country."],
];
goals.forEach(([icn, h, d], i) => {
  const y = 2.2 + i * 1.6;
  s.addShape(pres.shapes.OVAL, { x: 0.6, y, w: 0.9, h: 0.9, fill: { color: i === 2 ? HEX.coral : HEX.mint }, line: { type: "none" }, objectName: `a${2 + i}_dot` });
  s.addImage({ path: ic(icn, i === 2 ? "white" : "navy"), x: 0.84, y: y + 0.24, w: 0.42, h: 0.42, objectName: `a${2 + i}_icon`, altText: h });
  T(s, h, { x: 1.85, y: y - 0.05, w: 6, h: 0.5, fontSize: 22, bold: true, color: "FFFFFF", objectName: `a${2 + i}_h` });
  T(s, d, { x: 1.85, y: y + 0.42, w: 6.2, h: 0.8, fontSize: 16, color: HEX.mutedDark, objectName: `a${2 + i}_d` });
});
s.addNotes("Finally, here's what we hope to achieve. In six months, we want to have a group of loyal customers who use NutriPill and talk about it online. In twelve months, we want to reach more people online and double the number of customers we have. And in the long term, our goal is to become a well-known brand in our city first, and then grow across the whole country. To sum up, NutriPill is a simple answer to a problem that a lot of us have every day. Thank you very much for listening. Do you have any questions?");

(async () => {
  const out = path.join(__dirname, "NutriPill.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("wrote", out);
})();
