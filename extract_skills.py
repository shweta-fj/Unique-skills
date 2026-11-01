"""Extract unique, cleaned skills from curstdata_profiles.json.gz (NDJSON) into a plain JSON list.

Cleaning: NFKC unicode normalisation (fancy fonts -> plain), whitespace collapse, strip leading
bullets/emoji/#/punctuation and trailing punctuation (keeping "+", "#" and balanced ")"), then
group on a key that ignores case, spaces, hyphens and punctuation ("Java Script" == "JavaScript").

Usage: python -I extract_skills.py [--input PATH] [--output PATH] [--limit N]
"""
import argparse
import gzip
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = re.compile(r"\s+")
MAX_LEN = 100  # longer entries are sentences / pasted text, not skills


def clean(s):
    """Return the cleaned display form of a raw skill ('' if nothing usable remains)."""
    s = WS.sub(" ", unicodedata.normalize("NFKC", s)).strip()
    # leading junk: bullets, emoji, '#', '-', quotes... (keep ".NET"-style leading dot)
    i = 0
    while i < len(s) and not s[i].isalnum() and not (s[i] == "." and i + 1 < len(s) and s[i + 1].isalnum()):
        i += 1
    s = s[i:]
    # trailing junk: keep alnum, '+', '#', and ')' only when it closes a '('
    while s:
        c = s[-1]
        if c.isalnum() or c in "+#" or (c == ")" and s.count("(") >= s.count(")")):
            break
        s = s[:-1]
    return s.strip()


def key(s):
    """Grouping key: case/space/hyphen/punctuation-insensitive; keeps '+' and '#' (C++, C#)."""
    return "".join(ch for ch in s.casefold() if ch.isalnum() or ch in "+#")


def iter_skills(path, limit=None):
    """Yield (record_index, raw_skills_list_or_None, is_bad_line) per non-blank line."""
    read = 0
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            if limit is not None and read >= limit:
                break
            line = line.strip()
            if not line:
                continue
            read += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                yield None, True
                continue
            skills = rec.get("skills") if isinstance(rec, dict) else None
            yield (skills if isinstance(skills, list) else None), False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(HERE / "curstdata_profiles.json.gz"))
    ap.add_argument("--output", default=str(HERE / "unique_skills.json"))
    ap.add_argument("--limit", type=int, default=None, help="max records to read")
    args = ap.parse_args()

    spellings = defaultdict(Counter)  # key -> Counter of cleaned spellings
    counts = Counter()
    read = with_skills = bad = dropped_empty = dropped_long = 0

    for skills, is_bad in iter_skills(args.input, args.limit):
        read += 1
        if is_bad:
            bad += 1
            continue
        if skills is None:
            continue
        found = False
        for raw in skills:
            if not isinstance(raw, str):
                continue
            s = clean(raw)
            k = key(s)
            if not k:
                dropped_empty += 1
                continue
            if len(s) > MAX_LEN:
                dropped_long += 1
                continue
            found = True
            spellings[k][s] += 1
            counts[k] += 1
        with_skills += found

    ordered = sorted(counts, key=lambda k: (-counts[k], k))
    result = [spellings[k].most_common(1)[0][0] for k in ordered]

    with open(args.output, "w", encoding="utf-8") as out:
        json.dump(result, out, ensure_ascii=False, indent=2)

    print(f"records read: {read}, with skills: {with_skills}, malformed: {bad}")
    print(f"dropped (empty after cleaning): {dropped_empty}, dropped (> {MAX_LEN} chars): {dropped_long}")
    print(f"unique skills: {len(result)} -> {args.output}")


if __name__ == "__main__":
    main()
