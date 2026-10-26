// Generates logo, illustrations, backgrounds and icons as PNGs
const sharp = require("sharp");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const fs = require("fs");
const path = require("path");
const OUT = path.join(__dirname, "assets");
fs.mkdirSync(OUT, { recursive: true });

const NAVY = "#0B1F3A", NAVY2 = "#123A6B", MINT = "#14C9A1", MINT2 = "#0FA888", CORAL = "#FF6B4A";

const capsule = (id, w = 520, rot = -35) => `
  <defs>
    <linearGradient id="${id}m" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3FE6C0"/><stop offset="1" stop-color="${MINT2}"/></linearGradient>
    <linearGradient id="${id}w" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#D9E4EF"/></linearGradient>
    <clipPath id="${id}c"><rect x="0" y="0" width="${w}" height="${w * 0.4}" rx="${w * 0.2}"/></clipPath>
  </defs>
  <g transform="rotate(${rot} ${w / 2} ${w * 0.2})">
    <g clip-path="url(#${id}c)">
      <rect x="0" y="0" width="${w / 2}" height="${w * 0.4}" fill="url(#${id}m)"/>
      <rect x="${w / 2}" y="0" width="${w / 2}" height="${w * 0.4}" fill="url(#${id}w)"/>
      <rect x="${w * 0.08}" y="${w * 0.07}" width="${w * 0.84}" height="${w * 0.06}" rx="${w * 0.03}" fill="#FFFFFF" opacity="0.55"/>
    </g>
    <line x1="${w / 2}" y1="0" x2="${w / 2}" y2="${w * 0.4}" stroke="${NAVY}" stroke-opacity="0.12" stroke-width="${w * 0.012}"/>
  </g>`;

async function svg(name, svgStr, w, h) {
  await sharp(Buffer.from(svgStr)).resize(w, h).png().toFile(path.join(OUT, name));
}

async function main() {
  // Logo mark (capsule with leaf spark)
  const mark = (dark) => `<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="-40 -170 600 600">
    ${capsule("lm", 520, -40)}
    <g transform="translate(400 -120)"><path d="M0 60 C 0 20, 30 0, 80 0 C 80 50, 55 75, 10 75 Z" fill="${CORAL}"/><path d="M8 68 L 60 18" stroke="${dark ? NAVY : "#FFFFFF"}" stroke-width="6" stroke-linecap="round" opacity="0.6"/></g>
  </svg>`;
  await svg("logo-mark.png", mark(true), 600, 600);

  const wordmark = (dark) => `<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="500" viewBox="0 0 1800 500">
    <g transform="translate(30 190) scale(0.62)">${capsule("wm", 520, -40)}
      <g transform="translate(395 -110)"><path d="M0 60 C 0 20, 30 0, 80 0 C 80 50, 55 75, 10 75 Z" fill="${CORAL}"/></g></g>
    <text x="440" y="330" font-family="Inter" font-weight="900" font-size="250" letter-spacing="-6" fill="${dark ? NAVY : "#FFFFFF"}">Nutri<tspan fill="${MINT}">Pill</tspan></text>
  </svg>`;
  await svg("logo-dark.png", wordmark(true), 1800, 500);
  await svg("logo-light.png", wordmark(false), 1800, 500);

  // Hero illustration: big capsule + floating pills + glow
  const hero = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" viewBox="0 0 1200 1200">
    <defs><radialGradient id="g" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="${MINT}" stop-opacity="0.55"/><stop offset="1" stop-color="${MINT}" stop-opacity="0"/></radialGradient>
    <filter id="s" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="30" stdDeviation="30" flood-color="#000" flood-opacity="0.35"/></filter></defs>
    <circle cx="600" cy="600" r="560" fill="url(#g)"/>
    <circle cx="600" cy="600" r="380" fill="none" stroke="#FFFFFF" stroke-opacity="0.12" stroke-width="3"/>
    <circle cx="600" cy="600" r="480" fill="none" stroke="#FFFFFF" stroke-opacity="0.07" stroke-width="3" stroke-dasharray="6 18"/>
    <g filter="url(#s)" transform="translate(190 436)">${capsule("h", 820, -35)}</g>
    <g transform="translate(860 230) scale(0.32)">${capsule("h2", 520, 25)}</g>
    <g transform="translate(170 260) scale(0.22)">${capsule("h3", 520, 60)}</g>
    <g transform="translate(880 880) scale(0.2)">${capsule("h4", 520, -70)}</g>
    <circle cx="300" cy="900" r="18" fill="${CORAL}"/><circle cx="980" cy="560" r="12" fill="#FFFFFF" opacity="0.8"/>
    <circle cx="420" cy="180" r="10" fill="${MINT}"/><circle cx="1040" cy="760" r="22" fill="${MINT}" opacity="0.6"/>
  </svg>`;
  await svg("hero.png", hero, 1200, 1200);

  // Light-slide illustration (pill on soft disc)
  const heroLight = `<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1000" viewBox="0 0 1000 1000">
    <defs><linearGradient id="d" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#E3FAF4"/><stop offset="1" stop-color="#D6E6F7"/></linearGradient>
    <filter id="s" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="25" stdDeviation="25" flood-color="${NAVY}" flood-opacity="0.25"/></filter></defs>
    <circle cx="500" cy="500" r="440" fill="url(#d)"/>
    <circle cx="500" cy="500" r="470" fill="none" stroke="${MINT}" stroke-opacity="0.35" stroke-width="4" stroke-dasharray="4 16"/>
    <g filter="url(#s)" transform="translate(150 360)">${capsule("l", 700, -35)}</g>
    <circle cx="210" cy="250" r="22" fill="${CORAL}"/><circle cx="800" cy="780" r="16" fill="${MINT}"/><circle cx="820" cy="230" r="10" fill="${NAVY}" opacity="0.4"/>
  </svg>`;
  await svg("hero-light.png", heroLight, 1000, 1000);

  // Backgrounds
  const dark = `<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080">
    <defs><linearGradient id="b" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#081830"/><stop offset="1" stop-color="${NAVY2}"/></linearGradient>
    <radialGradient id="r1" cx="0.85" cy="0.1" r="0.6"><stop offset="0" stop-color="${MINT}" stop-opacity="0.28"/><stop offset="1" stop-color="${MINT}" stop-opacity="0"/></radialGradient>
    <radialGradient id="r2" cx="0.05" cy="1" r="0.55"><stop offset="0" stop-color="#2A6BD1" stop-opacity="0.35"/><stop offset="1" stop-color="#2A6BD1" stop-opacity="0"/></radialGradient>
    <pattern id="p" width="40" height="40" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.4" fill="#FFFFFF" opacity="0.06"/></pattern></defs>
    <rect width="1920" height="1080" fill="url(#b)"/><rect width="1920" height="1080" fill="url(#r1)"/><rect width="1920" height="1080" fill="url(#r2)"/><rect width="1920" height="1080" fill="url(#p)"/>
  </svg>`;
  await svg("bg-dark.png", dark, 1920, 1080);
  const light = `<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080">
    <defs><radialGradient id="r1" cx="1" cy="1" r="0.6"><stop offset="0" stop-color="${MINT}" stop-opacity="0.14"/><stop offset="1" stop-color="${MINT}" stop-opacity="0"/></radialGradient>
    <radialGradient id="r2" cx="0" cy="0" r="0.5"><stop offset="0" stop-color="#2A6BD1" stop-opacity="0.07"/><stop offset="1" stop-color="#2A6BD1" stop-opacity="0"/></radialGradient></defs>
    <rect width="1920" height="1080" fill="#FFFFFF"/><rect width="1920" height="1080" fill="url(#r1)"/><rect width="1920" height="1080" fill="url(#r2)"/>
  </svg>`;
  await svg("bg-light.png", light, 1920, 1080);

  // Icons
  const fa = require("react-icons/fa");
  const icons = {
    clock: "FaClock", battery: "FaBatteryQuarter", brain: "FaBrain", apple: "FaAppleAlt", bolt: "FaBolt",
    suitcase: "FaSuitcaseRolling", lightbulb: "FaLightbulb", heart: "FaHeartbeat", grad: "FaGraduationCap",
    briefcase: "FaBriefcase", run: "FaRunning", coins: "FaCoins", share: "FaShareAlt", tag: "FaTag",
    camera: "FaCameraRetro", star: "FaStar", gift: "FaGift", users: "FaUsers", check: "FaCheck",
    handshake: "FaHandshake", instagram: "FaInstagram", tiktok: "FaTiktok", youtube: "FaYoutube",
    flag: "FaFlag", chart: "FaChartLine", trophy: "FaTrophy", question: "FaQuestion", utensils: "FaUtensils",
  };
  const colors = { navy: NAVY, mint: MINT, white: "#FFFFFF", coral: CORAL };
  for (const [k, comp] of Object.entries(icons)) {
    for (const [cn, c] of Object.entries(colors)) {
      const s = renderToStaticMarkup(React.createElement(fa[comp], { color: c, size: 512 }));
      await sharp(Buffer.from(s)).resize(512, 512, { fit: "contain", background: { r: 0, g: 0, b: 0, alpha: 0 } }).png().toFile(path.join(OUT, `ic-${k}-${cn}.png`));
    }
  }
  console.log("assets done");
}
main();
