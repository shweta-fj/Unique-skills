# Skills → Icons

Two Python scripts that turn a raw LinkedIn-style profiles file into a clean list of unique skills, and then attach an icon link to every skill.

```
curstdata_profiles.json.gz        (raw profiles, ~17 GB)
        │
        ▼  extract_skills.py
unique_skills.json                (cleaned, de-duplicated skills, most frequent first)
        │
        ▼  skills_to_icons.py
iconsList_final.json              (every skill + icon link, or null)
```

The two scripts do not import each other. They are connected only by `unique_skills.json`.

## Requirements

- Python 3.8 or newer. No extra packages: both scripts use only the standard library.
- Internet access the first time `skills_to_icons.py` runs (it downloads small icon-name lists from Iconify).
- Put both scripts, and `curstdata_profiles.json.gz`, in the same folder.

## Step 1 - extract the unique skills (`extract_skills.py`)

```
python extract_skills.py
```

Reads the profiles file one line at a time (so the 17 GB file never has to fit in memory) and writes `unique_skills.json`.

What it does to each skill:
- converts fancy-font text to plain letters (Unicode NFKC) and collapses repeated spaces
- strips leading bullets, emoji and `#`, and trailing punctuation (it keeps `+`, `#` and a closing `)` that matches an opening `(`, so `C++`, `C#` and `Python (Programming Language)` survive)
- groups spellings that differ only by case, spaces, hyphens or punctuation (`Java Script` = `JavaScript`) and keeps the most common spelling
- drops entries that are empty after cleaning or longer than 100 characters (sentences, pasted text)

Options (all optional):

| Option | Default | Meaning |
|---|---|---|
| `--input PATH` | `curstdata_profiles.json.gz` next to the script | the raw profiles file |
| `--output PATH` | `unique_skills.json` next to the script | where to write the list |
| `--limit N` | all | read only the first N profiles (useful for a quick test) |

Output: a JSON list of skill-name strings, sorted by how often each skill appears. The run used for this project produced **533,960** unique skills from 859,304 profiles.

## Step 2 - attach an icon to every skill (`skills_to_icons.py`)

```
python skills_to_icons.py unique_skills.json iconsList_final.json --base-url https://shweta-fj.github.io/skills-icon/
```

Output: a JSON list with one entry per skill. `icon` is a link, or `null` when no icon was found:

```json
[
  { "skill": "Microsoft Excel", "icon": "https://shweta-fj.github.io/skills-icon/thesvg-color/microsoft-excel.svg" },
  { "skill": "Attention to Detail", "icon": "https://shweta-fj.github.io/skills-icon/lucide/scan-search.svg" },
  { "skill": "Lead Generation", "icon": null }
]
```

### Choose how the `icon` link is written

| Command ending | `icon` value | Use it when |
|---|---|---|
| *(nothing)* | `https://api.iconify.design/devicon/react.svg` | quick tests only. The links load live from Iconify, which can block you if many are requested (Cloudflare error 1015 / HTTP 429). |
| `--base-url https://your-host/path/` | `https://your-host/path/devicon/react.svg` | **the normal choice.** You host the SVG files yourself and the JSON points at them. |
| `--local` | `icons/devicon/react.svg` | also downloads all the SVG files into an `icons/` folder next to the script, so you can upload them to your host. Cannot be combined with `--base-url`. |

Typical workflow:
1. Run once with `--local` to create the `icons/` folder (about 3,400 SVG files, 8 MB). It downloads in batches of 40 with pauses, so it takes a few minutes.
2. Upload the contents of `icons/` to your host (this project uses GitHub Pages: repo `shweta-fj/skills-icon`, with the pack folders at the top level of the repo).
3. Run again with `--base-url` set to where you uploaded them.
4. To move to another host later, run step 3 again with the new address. Nothing else changes.

### How a skill is matched

1. **Icon-name lists.** On first run the script downloads one list of icon names per pack into `icon_lists/`: devicon, simple-icons, logos, skill-icons, fa6-brands, cib, thesvg-color, selfhst (in this priority order, first match wins). No images are downloaded at this point.
2. **Brand logo.** Each skill name is cleaned to a key (lower-case letters and digits only) and looked up. It tries the full name, the name without text in brackets, the part after `Label: `, the first item before a `/`, `Amazon X` as `AWS X`, and the name without a trailing `Framework`, `API`, `APIs` or `Products`. Text inside brackets is never used as a candidate (so `(SAP)` or `(DBT)` cannot hijack a skill). A hand-written alias list maps names such as `reactjs` to `react`, and a blocklist stops ambiguous words (Unity, Spark, Teamwork, Make ...) from getting a brand logo.
3. **Reviewed soft-skill icons.** About 86 common soft skills (Communication, Leadership, Time Management ...) have a hand-picked icon from the `lucide` set. These are checked before the keyword rules.
4. **Generic icon.** If there is no brand logo, keyword rules choose a generic `lucide` icon (for example *Machine Learning* → brain, *SQL* → database).
5. **Otherwise** the icon is `null`.

Result on the full list: **237,227** skills with an icon (7,662 brand logos, the rest generic or reviewed soft-skill icons) and **296,733** with `null`. These are made of **3,406** distinct SVG files.

### Folders the script creates

| Folder | Created when | Contents |
|---|---|---|
| `icon_lists/` | first run | the 8 icon-name lists from Iconify (a few hundred KB) |
| `icons/` | only with `--local` | the 3,406 SVG files, one folder per pack |

## Troubleshooting

- **`HTTP Error 429` or a Cloudflare "Error 1015 - rate limited" page:** Iconify is temporarily blocking your IP because of too many requests. Wait a while (minutes to an hour) and run again. The script retries the first download on its own, and downloads icon files in small batches to avoid this.
- **A link returns 404:** the SVG hasn't been uploaded to the host yet, or the host's page is not switched on (for GitHub Pages: repo Settings → Pages → Deploy from a branch → `main` / root).
- **Accented or non-English skills look garbled on Windows:** both scripts read and write UTF-8 explicitly. Open the JSON in an editor that uses UTF-8.
- **`FileNotFoundError` for `curstdata_profiles.json.gz`:** put it next to `extract_skills.py`, or pass `--input PATH`.

## Good to know

- **Trademarks.** The icon packs are open-licensed, but the brand marks inside them belong to their owners. Get a legal review before using brand logos in a commercial product.
- **Limits of free hosting.** GitHub Pages has a soft limit of 100 GB of bandwidth a month and is not meant for hosting a business. Fine for testing; check the terms before production use.
- **Coverage.** About 1.4% of skills get a real brand logo, 43% get a generic icon and 55.6% get `null`. Most skills are business or soft skills that have no logo to find. Missing brand logos can be added by extending the alias list in `skills_to_icons.py`.
