// Render every pandoc math span to static KaTeX HTML at build time.
// A LaTeX error fails the build instead of shipping broken math.
// Usage: node render_math.mjs in.html out.html macros.json
import { readFileSync, writeFileSync } from "node:fs";
import katex from "katex";

const [inPath, outPath, macrosPath] = process.argv.slice(2);
const macros = macrosPath ? JSON.parse(readFileSync(macrosPath, "utf8")) : {};
const html = readFileSync(inPath, "utf8");

const unescape = (s) =>
  s.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'").replace(/&amp;/g, "&");

let failures = 0;
const out = html.replace(
  /<span class="math (inline|display)">([\s\S]*?)<\/span>/g,
  (_, mode, body) => {
    const tex = unescape(body);
    try {
      const rendered = katex.renderToString(tex, {
        displayMode: mode === "display",
        throwOnError: true,
        strict: false,
        trust: false,
        macros: { ...macros },
      });
      return mode === "display" ? `<span class="math-display">${rendered}</span>` : rendered;
    } catch (err) {
      failures += 1;
      console.error(`MATHERR ${inPath}: ${err.message}\n    ${tex.slice(0, 200)}`);
      return `<code class="math-error">${body}</code>`;
    }
  },
);

writeFileSync(outPath, out);
process.exit(failures ? 1 : 0);
