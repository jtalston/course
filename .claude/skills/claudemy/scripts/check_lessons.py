"""Check every lesson in <workspace>/class/ before its audio is rendered.

A lesson passes when its script is two-host dialogue of about 2 minutes with
no banned language, and its card has the standard sections and cites only
pages that are actually on disk in <workspace>/raw/. A citation to a page the
class never read is how invented sources get in, so it is a hard fail.

Usage: python3 check_lessons.py <workspace> [lesson-folder ...]   (default: all)
Exit 1 if any lesson fails.
"""
import re, sys
from pathlib import Path

CARD_SECTIONS = ["**Listen:**", "The idea, in three lines", "**Impact:**", "**Who says it:**",
                 "**Try it**", "**Rule to keep**", "**Skip**",
                 "**Go deeper (optional)**"]
# Demand words land as pressure on many learners (and on PDA profiles as a shutdown trigger).
DEMAND = re.compile(r"\b(you need to|you must|you should|make sure|you have to|don't forget)\b", re.I)
DASH = re.compile(r"—|–|(?<!<!)--(?!>)")
TAG = re.compile(r"\[[a-z ]+\]")
# 280 to 350 words renders at about 2:00 to 2:30. Measured: 347 words ran 2:27, 371 ran 2:32.
WORDS_MIN, WORDS_MAX, TAGS_MAX = 280, 350, 3


# Balanced parentheses stay in the url (Wikipedia's Mercury_(planet)); a lone ")" ends
# it, as in a markdown link. Backticks, brackets and angle brackets wrap urls, never end them.
URL = re.compile(r"https?://(?:[^\s()<>\[\]`]|\([^\s()<>]*\))+")
# Bold, code spans and sentence ends trail urls in markdown; none of that is part of the url.
TRAILING = ".,;:!?*_'\"`"


def cited_urls(text):
    return [u.rstrip(TRAILING) for u in URL.findall(text)]


def same_page(url):
    """One key per page: scheme, www., #fragment and a trailing slash don't change
    the page. Exact matching failed valid citations and sent the writer round the
    fix loop up to three times for nothing. Trailing marks come off both sides,
    so a url that really ends in "_" or "!" still matches itself."""
    url = url.rstrip(TRAILING)
    m = re.match(r"https?://([^/?#]+)([^#]*)", url, re.I)
    if not m:
        return url
    path, q, query = m.group(2).partition("?")
    return m.group(1).lower().removeprefix("www.") + path.rstrip("/") + q + query


def scraped_urls(ws):
    # scrape.py writes UTF-8; reading in the locale's encoding crashed on Windows-style locales.
    return {line[5:].strip() for f in ws.glob("raw/*/*.md")
            for line in f.read_text(encoding="utf-8", errors="replace").splitlines()[:12] if line.startswith("url: ")}


def banned(text):
    found = []
    if DASH.search(text):
        found.append("emdash or double hyphen")
    m = DEMAND.search(text)
    if m:
        found.append(f"demand phrase {m.group(0)!r}")
    return found


# ASD-STE100 mode (sources.json "style": "ste100"; see references/ste100.md).
STE_PROC, STE_DESC = 20, 25
CONTRACTION = re.compile(r"\b\w+'(s|re|ve|ll|d|t|m)\b", re.I)
ING_OK = {"thing", "things", "nothing", "something", "anything", "everything", "string", "strings",
          "during", "bring", "single", "king", "spring", "ring", "wing", "morning", "evening",
          "missing", "pending", "existing", "following", "remaining", "working"}
PASSIVE = re.compile(r"\b(is|are|was|were|be|been|being)\s+(\w+ed|written|done|made|lost|kept|shown|given|taken|seen|known|built|set)\b", re.I)


def sentences(text):
    """Prose sentences: code, urls and markdown markup removed; a list item or line break ends one."""
    text = re.sub(r"```.*?```|`[^`\n]*`", "CODE", text, flags=re.S)
    text = URL.sub("URL", text)
    text = re.sub(r"[*_#>]+", " ", text)
    out = []
    for line in text.splitlines():
        line = re.sub(r"^\s*(?:[-+]|\d+\.)\s+", "", line)
        out += [s.strip() for s in re.split(r"(?<=[.!?:])\s+", line) if len(s.split()) > 1]
    return out


def ste_problems(text, limit, where):
    long = [s for s in sentences(text) if len(s.split()) > limit]
    return [f"STE {where}: {len(s.split())} words, max {limit}: {s[:60]!r}" for s in long]


def ste_warnings(text):
    text = URL.sub("", re.sub(r"```.*?```|`[^`\n]*`", "", text, flags=re.S))
    ing = sorted({w.lower() for w in re.findall(r"\b[A-Za-z]+ing\b", text)} - ING_OK)
    warn = [f"-ing words: {', '.join(ing[:8])}"] if ing else []
    passive = PASSIVE.findall(text)
    if passive:
        warn.append(f"possible passive: {', '.join(' '.join(p) for p in passive[:4])}")
    return warn


def check_script(text):
    lines = [l for l in text.splitlines() if l.strip()]
    bad = [l for l in lines if not re.match(r"^[AB]: \S", l)]
    words = len(re.sub(r"^[AB]:", "", text, flags=re.M).split())
    problems = [f"{len(bad)} lines not 'A:'/'B:' (first: {bad[0][:40]!r})"] if bad else []
    if not WORDS_MIN <= words <= WORDS_MAX:
        problems.append(f"{words} words, want {WORDS_MIN} to {WORDS_MAX} (about 2 minutes)")
    if len(TAG.findall(text)) > TAGS_MAX:
        problems.append(f"{len(TAG.findall(text))} audio tags, max {TAGS_MAX}")
    return problems + [f"script: {m}" for m in banned(text)], words


def check_script_ste(text):
    spoken = re.sub(r"^[AB]:\s*", "", text, flags=re.M)
    problems = ste_problems(spoken, STE_DESC, "script")
    if TAG.search(text):
        problems.append("STE script: audio tags are not used in STE mode")
    if CONTRACTION.search(spoken):
        problems.append(f"STE script: contractions ({', '.join([m.group(0) for m in CONTRACTION.finditer(spoken)][:5])})")
    return problems


def check_card_ste(text):
    body = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    m = re.search(r"\*\*Try it\*\*(.*?)\*\*Rule to keep\*\*", body, flags=re.S)
    tryit = m.group(1) if m else ""
    rest = body.replace(tryit, "") if tryit else body
    rest = re.sub(r"^\*\*Go deeper.*", "", rest, flags=re.S | re.M)
    problems = ste_problems(tryit, STE_PROC, "Try it") + ste_problems(rest, STE_DESC, "card")
    prose = re.sub(r"```.*?```|`[^`\n]*`", "", body, flags=re.S)
    if CONTRACTION.search(prose):
        problems.append(f"STE card: contractions ({', '.join([m.group(0) for m in CONTRACTION.finditer(prose)][:5])})")
    return problems


def check_card(text, urls):
    # Every check runs on what the learner sees. HTML comments (editor notes, a
    # commented-out draft section) are not content: a section that exists only
    # inside one is missing, a demand phrase inside one is not a fail.
    body = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    problems = [f"card missing {s!r}" for s in CARD_SECTIONS if s not in body]
    # Command-line flags (git push --force-with-lease) are code, not prose dashes:
    # the dash rule skips fenced blocks and `code spans`, nothing else.
    prose = re.sub(r"```.*?```|`[^`\n]*`", "", body, flags=re.S)
    problems += [f"card: {m}" for m in banned(prose)]
    cited = cited_urls(body)
    if not cited:
        problems.append("card cites no source")
    known = {same_page(u) for u in urls}
    problems += [f"card cites a page that is not in raw/: {u}" for u in cited if same_page(u) not in known]
    return problems


def check_plan(ws, urls):
    """The plan cites pages too. In the first full test, checking it by hand caught
    3 stories credited to the wrong page; a url not on disk is the part a script can catch."""
    plan = ws / "class" / "lesson-plan.md"
    if not plan.exists():
        return 0
    cited = set(cited_urls(plan.read_text(encoding="utf-8")))
    if not cited:
        # A plan that names sources without links has nothing this check can test; "ok" read as a pass.
        print("skip lesson-plan.md (cites no urls, nothing to check)")
        return 0
    known = {same_page(u) for u in urls}
    missing = sorted(u for u in cited if same_page(u) not in known)
    print(f"{'FAIL' if missing else 'ok  '} lesson-plan.md ({len(cited)} urls)")
    for u in missing:
        print(f"     plan cites a page that is not in raw/: {u}")
    return bool(missing)


def class_style(ws):
    try:
        import json
        return json.loads((ws / "sources.json").read_text(encoding="utf-8")).get("style", "")
    except (OSError, ValueError):
        return ""


def main(ws, folders):
    # A url or name the console can't show must not crash the report.
    sys.stdout.reconfigure(errors="replace")
    urls = scraped_urls(ws)
    ste = class_style(ws).lower() == "ste100"
    failed = check_plan(ws, urls)
    for d in folders:
        script, card = d / "script.txt", d / "card.md"
        if not (script.exists() and card.exists()):
            print(f"FAIL {d.name}: missing script.txt or card.md")
            failed += 1
            continue
        s_text, c_text = script.read_text(encoding="utf-8"), card.read_text(encoding="utf-8")
        problems, words = check_script(s_text)
        problems += check_card(c_text, urls)
        warnings = []
        if ste:
            problems += check_script_ste(s_text) + check_card_ste(c_text)
            warnings = ste_warnings(s_text + "\n" + c_text)
        print(f"{'FAIL' if problems else 'ok  '} {d.name} ({words} words{', STE' if ste else ''})")
        for p in problems:
            print(f"     {p}")
        for w in warnings:
            print(f"     warn {w}")
        failed += bool(problems)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    ws = Path(sys.argv[1]).expanduser().resolve()
    folders = [Path(a) for a in sys.argv[2:]] or sorted(p for p in (ws / "class").glob("[0-9][0-9]-*") if p.is_dir())
    main(ws, folders)
