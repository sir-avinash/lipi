#!/usr/bin/env python3
"""Enforce one vocabulary and one notation across the whole book.

    python tools/check_terms.py          # exit 1 if any rule is violated

Rules live in `terms.toml` at the repository root. Each rule bans a spelling,
a synonym or a notation variant and names the form the glossary prescribes.
The check covers chapter text, figure scripts, notebook sources and skills,
so a symbol or a term cannot drift between the prose, a plot label and a
notebook cell.

    [[rule]]
    pattern = 'inertial frame'        # Python regular expression
    use = 'world frame'               # what to write instead
    where = ['chapters', 'notebooks', 'figures', 'skills']   # optional
    math = false                      # optional: true = only inside $...$,
                                      # false = only outside, omitted = both
    ignore_case = true                # optional
    allow = ['inertial frame of the gyroscope']   # optional literal exceptions
    code = true                       # optional: also check inside Markdown
                                      # code spans and fences (skipped by default)

`allow` entries are literal substrings: a match is ignored when its line
contains one of them. `where` may also name 'verify'. Patterns are searched
with re.MULTILINE, so `^` and `$` anchor to lines.

Text between a line containing `terms:off` and the next line containing
`terms:on` is never checked. Write the markers as comments
(`<!-- terms:off -->` in Markdown, `# terms:off` in Python). The glossary uses
them around its table of banned variants, and a chapter may use them around a
quotation that has to keep its original wording.
"""
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = {
    "chapters": ("chapters", "*.md"),
    "figures": ("figures/src", "*.py"),
    "notebooks": ("notebooks/src", "*.py"),
    "skills": ("skills", "*/SKILL.md"),
    "verify": ("verify", "*.py"),
}
MATH = re.compile(r"\$\$.*?\$\$|\$[^$\n]+\$", re.S)
CODE = re.compile(r"```.*?```|`[^`\n]+`", re.S)
OFF = re.compile(r"^[^\n]*terms:off.*?(?:^[^\n]*terms:on[^\n]*$|\Z)", re.S | re.M)


def spans(text: str, regex: re.Pattern) -> list[tuple[int, int]]:
    return [m.span() for m in regex.finditer(text)]


def inside(pos: int, ranges: list[tuple[int, int]]) -> bool:
    return any(a <= pos < b for a, b in ranges)


def main() -> None:
    cfg = tomllib.loads((ROOT / "terms.toml").read_text(encoding="utf-8"))
    problems = []
    for rule in cfg.get("rule", []):
        flags = re.M | (re.I if rule.get("ignore_case") else 0)
        regex = re.compile(rule["pattern"], flags)
        for where in rule.get("where", ["chapters", "figures", "notebooks", "skills"]):
            folder, glob = SOURCES[where]
            for path in sorted((ROOT / folder).glob(glob)):
                text = path.read_text(encoding="utf-8")
                is_markdown = path.suffix == ".md"
                math = spans(text, MATH)
                code = spans(text, CODE) if is_markdown else []
                off = spans(text, OFF)
                for m in regex.finditer(text):
                    if inside(m.start(), off):
                        continue
                    if is_markdown and not rule.get("code") and inside(m.start(), code):
                        continue
                    if "math" in rule and inside(m.start(), math) != rule["math"]:
                        continue
                    line_start = text.rfind("\n", 0, m.start()) + 1
                    line_end = text.find("\n", m.end())
                    line = text[line_start:line_end if line_end != -1 else None]
                    if any(ok in line for ok in rule.get("allow", [])):
                        continue
                    lineno = text.count("\n", 0, m.start()) + 1
                    problems.append(f'{path.relative_to(ROOT)}:{lineno}: "{m.group(0)}" -> use "{rule["use"]}"')
    for p in problems:
        print(p)
    print(f"{len(cfg.get('rule', []))} rules, {len(problems)} violations")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
