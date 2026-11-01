"""skills_to_icons.py - ONE script: match every skill to an icon and write the final JSON.

Input : a JSON list of skill names (unique_skills.json)
Output: a JSON list of {"skill": ..., "icon": ...} for ALL skills.
        icon = the icon URL, or null when no icon was found.

Usage:
  python skills_to_icons.py unique_skills.json iconsList_final.json            (icon = Iconify URL)
  python skills_to_icons.py unique_skills.json iconsList_final.json --local    (also downloads the SVGs into ./icons/
                                                                                and writes icon = "icons/<pack>/<name>.svg")
  python skills_to_icons.py unique_skills.json iconsList_final.json --base-url https://shweta-fj.github.io/skills-icon/
                                                                               (icon = <base-url><pack>/<name>.svg, for icons you host yourself;
                                                                                upload the SVGs from --local to that location)
First run downloads small icon-name lists from Iconify into ./icon_lists/ (needs internet).
"""
import json, re, sys, unicodedata, time, argparse

import os, urllib.request
ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon_lists") + os.sep
SETS = ["devicon", "simple-icons", "logos", "skill-icons", "fa6-brands", "cib", "thesvg-color", "selfhst"]   # priority order
API = "https://api.iconify.design/"

def key(s):
    s = unicodedata.normalize("NFKC", s).lower().replace("+", "plus").replace("#", "sharp").replace(".js", "js")
    return re.sub(r"[^a-z0-9]", "", s)

def ensure_icon_lists():
    """Download each pack's icon-name list from Iconify on first run (needs internet)."""
    os.makedirs(ICON_DIR, exist_ok=True)
    for p in SETS:
        path = f"{ICON_DIR}{p}.json"
        if not os.path.exists(path):
            print("downloading icon list:", p)
            for attempt in range(6):          # retry with a growing pause if Iconify says "too many requests" (429)
                try:
                    req = urllib.request.Request(f"{API}collection?prefix={p}", headers={"User-Agent": "Mozilla/5.0 skills-logo-script"})
                    with urllib.request.urlopen(req, timeout=60) as r:
                        data = r.read()
                    open(path, "wb").write(data)
                    break
                except Exception as ex:
                    print("  retry", attempt + 1, "-", ex); time.sleep(10 * (attempt + 1))
            else:
                raise SystemExit("could not download the icon list for " + p + " - try again in a few minutes")
            time.sleep(1)
ensure_icon_lists()

# icon key -> (prefix, name); devicon prefers -original, then -plain; skips wordmarks
icons = {}
VARIANT = re.compile(r"-(dark|light|reverse|mono|wordmark|(19|20)\d\d)$")
def rank(n):
    if n.endswith("-wordmark") or VARIANT.search(n): return 9
    if n.endswith("-original"): return 0
    if n.endswith("-plain"): return 1
    return 2
for p in SETS:
    d = json.load(open(f"{ICON_DIR}{p}.json", encoding="utf-8"))
    names = set(d.get("uncategorized", [])) | set(d.get("aliases", {}))
    for c in d.get("categories", {}).values(): names |= set(c)
    for n in sorted(names, key=rank):
        if rank(n) == 9: continue
        base = re.sub(r"-(original|plain|line)$", "", n)
        icons.setdefault(key(base), (p, n))

ALIASES = {  # skill key -> icon key
 "amazonwebservicesaws":"amazonwebservices","aws":"amazonwebservices","cascadingstylesheetscss":"css3","css":"css3",
 "html":"html5","html5":"html5","pythonprogramminglanguage":"python","python":"python","reactjs":"react","react":"react",
 "nodejs":"nodejs","angularjs":"angularjs","angular":"angular","vuejs":"vuejs","microsoftexcel":"microsoftexcel",
 "microsoftword":"microsoftword","microsoftpowerpoint":"microsoftpowerpoint","microsoftoffice":"microsoftoffice",
 "microsoftazure":"azure","azure":"azure","googlecloudplatformgcp":"googlecloud","googlecloudplatform":"googlecloud",
 "gcp":"googlecloud","cplusplus":"cplusplus","csharp":"csharp","cprogramminglanguage":"c","c":"c","javaprogramminglanguage":"java",
 "mysql":"mysql","postgresql":"postgresql","mongodb":"mongodb","docker":"docker","kubernetes":"kubernetes","git":"git",
 "github":"github","gitlab":"gitlab","linux":"linux","javascript":"javascript","typescript":"typescript","php":"php",
 "wordpress":"wordpress","photoshop":"photoshop","adobephotoshop":"photoshop","adobeillustrator":"illustrator",
 "adobeindesign":"indesign","figma":"figma","jira":"jira","tensorflow":"tensorflow","pytorch":"pytorch","pandas":"pandas",
 "numpy":"numpy","tableau":"tableau","powerbi":"powerbi","salesforce":"salesforce",
 "salesforcecrm":"salesforce","sap":"sap","jenkins":"jenkins","redis":"redis","firebase":"firebase","flutter":"flutter",
 "swift":"swift","kotlin":"kotlin","golang":"go","go":"go","rubyonrails":"rails","springboot":"spring","django":"django",
 "flask":"flask","bootstrap":"bootstrap","tailwindcss":"tailwindcss","jquery":"jquery","sass":"sass","graphql":"graphql",
 "r":"r","rprogramminglanguage":"r","matlab":"matlab","excel":"microsoftexcel","word":"microsoftword","powerpoint":"microsoftpowerpoint",
 "autocad":"autocad","solidworks":"solidworks","slack":"slack","trello":"trello","oracledatabase":"oracle","oracle":"oracle",
 "apachespark":"apachespark","hadoop":"apachehadoop","apachekafka":"apachekafka","terraform":"terraform","ansible":"ansible",
 "aws":"amazonwebservices","nextjs":"nextjs","expressjs":"express","mernstack":"mongodb","iot":None,
}
ALIASES = {k:v for k,v in ALIASES.items() if v}

# generic icons for non-brand skills (lucide set), first match wins
# ambiguous words that are also product names: never treat as a brand logo
BLOCK = set("lightning dash red ram rom text config binary log license image video audio zip pdf test todo tag default folder file code document table list chart book box web link home user users team group map search star heart mail phone key lock "
  "teamwork hack micro vector linear flux clarity fabric passport nano make shell opensource usertesting asterisk gin apex pdm r3 rtm yolo spark parcel corda cnn dbt clerk drizzle hardhat pwa arm unity framer".split())
ALIASES.update({
 "powerbi":"microsoftpowerbi","msexcel":"microsoftexcel","msword":"microsoftword","mspowerpoint":"microsoftpowerpoint",
 "msoffice":"microsoftoffice","microsoftoffice365":"microsoftoffice","office365":"microsoftoffice","microsoft365":"microsoftoffice",
 "outlook":"microsoftoutlook","sharepoint":"microsoftsharepoint","teams":"microsoftteams","msteams":"microsoftteams",
 "sqlserver":"microsoftsqlserver","mssqlserver":"microsoftsqlserver","mssql":"microsoftsqlserver",
 "gsuite":"googleworkspace","googledocs":"googledocs","googlesheets":"googlesheets",
 "tailwind":"tailwindcss","mongo":"mongodb","postgres":"postgresql","k8s":"kubernetes","js":"javascript","ts":"typescript",
 "aspnet":"dotnet","aspnetcore":"dotnet","net":"dotnet","netcore":"dotnet","dotnetcore":"dotnet","vue":"vuejs","nextjs":"nextjs",
 "chatgpt":"openai","gpt":"openai","powerautomate":"microsoftpowerautomate","powerapps":"microsoftpowerapps",
 "serviceNow".lower():"servicenow","workday":"workday","sap":"sap","sapabap":"sap","saphana":"saphana",
})
ALIASES.update({
 "corejava":"java","javaenterpriseedition":"java","javaserverpages":"java","jsp":"java","servlets":"java","servlet":"java","j2ee":"java","javaee":"java",
 "springframework":"spring","springmvc":"spring","springmvcframework":"spring",
 "netframework":"dotnet","aspnetmvc":"dotnet","aspnetwebapi":"dotnet","entityframework":"entityframeworkcore","ef":None,
 "windowsserver":"microsoftwindows","activedirectory":"microsoftwindows",
 "azurefunctions":"azure","azuredevopsserver":"azuredevops",
 "saperp":"sap","saphana":"sap","saps4hana":"sap","sapfico":"sap","sapimplementation":"sap","sapproducts":"sap","abap":"sap",
 "amazonec2":"awsec2","amazondynamodb":"dynamodb","amazonredshift":"awsredshift","amazoneks":"awseks","amazoncloudwatch":"awscloudwatch",
 "amazons3":"awss3","amazonlambda":"awslambda","amazonrds":"awsrds","amazonsqs":"awssqs","amazonsns":"awssns",
 "seleniumwebdriver":"selenium","seleniumtesting":"selenium","jmeter":"apachejmeter","postmanapi":"postman","swaggerapi":"swagger",
 "revit":"autodeskrevit","pyspark":"apachespark","dockerproducts":"docker","redhatlinux":"redhat","facebookads":"facebook",
 "djangorestframework":"djangorest","jsonwebtoken":"jwt","reacthooks":"react","hive":"apachehive","apachehive":"apachehive",
})
ALIASES = {k:v for k,v in ALIASES.items() if v}
ALIASES.update({"reduxjs":"redux","dbt":"dbt","datadbttooldbt":"dbt"})
CONCEPTS = [
 (r"\bsql\b|nosql|rdbms|dbms|database|data ?warehouse","database"),
 (r"machine learning|deep learning|neural network|\bnlp\b|natural language|computer vision|predictive model|mlops|\bllm\b|\brag\b|retrieval-augmented","brain"),
 (r"artificial intelligence|\bai\b|generative|gen ai|ai agents","bot"),
 (r"payroll|invoic|bookkeeping|cash flow|ledger|loans|mutual funds|investment|\bvaluation|venture capital|private equity|capital markets|payments","banknote"),
 (r"cloud","cloud"),
 (r"cyber|security|penetration|vulnerab|firewall|infosec|encrypt","shield"),
 (r"agile|scrum|kanban|sprint|lean |six sigma|continuous improvement|process improvement","refresh-cw"),
 (r"testing|test automation|test cases|quality assurance|\bqa\b|debug|defect","flask-conical"),
 (r"version control|ci/cd|continuous integration|continuous delivery|devops","git-branch"),
 (r"network|tcp/ip|protocol","network"),
 (r"blockchain|crypto","blocks"),
 (r"social media|blogging","share-2"),
 (r"\bapis?\b|\bsoap\b|webhook","webhook"),
 (r"algorithm|data structure|multithread","binary"),
 (r"embedded|microcontroller|electronics|\biot\b|internet of things|hardware","cpu"),
 (r"operating system|virtualization|infrastructure|system administration|servers?\b","server"),
 (r"automation|\brpa\b|robotic|workflow","workflow"),
 (r"web scraping|web application|web technolog|\bhtml","globe"),
 (r"\betl\b|^extract$|^transform$|business intelligence|dashboard|visuali[sz]ation|forecast|reporting|pivot","chart-column"),
 (r"litigation|court|intellectual property|mediation|dispute|legal","scale"),
 (r"real estate|construction|architecture","building"),
 (r"manufactur|automotive|mechanical","factory"),
 (r"e-?commerce|retail|merchandis","shopping-cart"),
 (r"user experience|\bux\b|usability|wireframe|wireframing|prototyp|illustration|typography|sketching","palette"),
]
CONCEPTS = [(re.compile(p, re.I), i) for p, i in CONCEPTS]

SOFT = [
 (r"communicat|speaking|presentation|writing|negotiat","message-circle"),
 (r"leader|managing|management|supervis|mentor|coaching","users"),
 (r"team|collaborat|interpersonal","users-round"),
 (r"problem|critical thinking|troubleshoot","puzzle"),
 (r"analy|research|statistic|data","bar-chart-3"),
 (r"customer|client|service|support","headset"),
 (r"sales|business development|marketing|advertis|seo","trending-up"),
 (r"project|planning|strategy|strategic|operations|time management","clipboard-list"),
 (r"financ|account|budget|audit|bank|tax","wallet"),
 (r"design|creative|graphic|photograph|video","palette"),
 (r"teach|train|educat|tutor","graduation-cap"),
 (r"health|nurs|medic|clinical","heart-pulse"),
 (r"legal|law|compliance|contract","scale"),
 (r"english|hindi|spanish|french|german|language|translat","languages"),
 (r"engineer|software|programming|develop|coding|cod(e|ing)","code"),
 (r"recruit|hiring|human resources|\bhr\b|talent","user-search"),
]
SOFT = [(re.compile(p, re.I), i) for p, i in SOFT]

def lookup(skill):
    base = re.sub(r"\s*\([^)]*\)", "", skill).strip()
    cands = [skill, base]
    if ':' in base:   # "Software Expertise: Xero" -> "Xero" (needs a 2+ word label before the colon)
        pre, post = base.split(':', 1)
        if len(pre.split()) >= 2: cands.append(post.strip())
    if '/' in base:   # "Adobe XD / Invision" -> first item only; avoids picking arbitrary items from long lists
        first = base.split('/')[0].strip()
        if len(key(first)) >= 3: cands.append(first)
    for c in list(cands):
        if c.lower().startswith('amazon '): cands.append('aws ' + c[7:])
        m = re.sub(r'\s+(framework|api|apis|products)$', '', c, flags=re.I)
        if m != c and len(key(m)) >= 5: cands.append(m)
    for cand in cands:   # parenthetical text is NOT used as a candidate (e.g. "(DBT)", "(CNN)", "(SAP)" are other things)
        k = key(cand)
        if k in BLOCK: continue
        k = ALIASES.get(k, k)
        if k in icons: return icons[k]
    return None

def enrich(skill):
    m = lookup(skill)
    if m:
        return dict(skill=skill, logo=f"{m[0]}:{m[1]}", logo_url=f"{API}{m[0]}/{m[1]}.svg", logo_type="brand")
    for rx, i in CONCEPTS + SOFT:
        if rx.search(skill):
            return dict(skill=skill, logo=f"lucide:{i}", logo_url=f"{API}lucide/{i}.svg", logo_type="generic")
    return dict(skill=skill, logo=None, logo_url=None, logo_type=None)



# ---- reviewed icons for common soft skills (override the keyword rules) ----
# Reviewed lucide icon for each soft skill in soft_skills_logos.json (one fitting icon per meaning, not just users/message)
SOFT_ICONS = {
"Account Management":"briefcase-business","Accountability":"badge-check","Active Learning":"book-open","Active Listening":"ear",
"Adaptability":"shuffle","Adaptability and Flexibility":"shuffle","Analytical Skills":"chart-line","Analytical Thinking":"chart-line",
"Attention to Detail":"scan-search","Business Communication":"message-square-text","Change Management":"refresh-cw","Coaching":"user-check",
"Collaboration":"users-round","Collaboration Skills":"users-round","Communication":"message-circle","Communication Skills":"message-circle",
"Conflict Management":"handshake","Conflict Resolution":"handshake","Creative Thinking":"lightbulb","Creativity":"lightbulb",
"Creativity and Innovation":"lightbulb","Critical Thinking":"brain","Critical Thinking Skills":"brain",
"Cross-Functional Collaboration":"users-round","Customer Relations":"headset","Customer Satisfaction":"smile","Customer Service":"headset",
"Decision Making Skills":"route","Dependability":"shield-check","Emotional Intelligence":"heart-handshake","Empathy":"heart",
"Facilitation":"presentation","Flexibility":"shuffle","Influencing":"megaphone","Initiative":"rocket","Instruction":"graduation-cap",
"Interpersonal Communication":"messages-square","Interpersonal relationship":"users-round","Interpersonal Skills":"users-round",
"Leadership":"crown","Leadership Skills":"crown","Learning Agility":"zap","Mentoring":"hand-helping","Motivation":"flame",
"Negotiation":"handshake","Networking":"network","Open-Mindedness":"door-open","Organization":"layout-list","Patience":"hourglass",
"People Management":"users","People Skills":"users-round","Persuasion":"megaphone","Planning":"calendar-check","Positive attitude":"smile",
"Presentation":"presentation","Presentation Skills":"presentation","Prioritization":"list-ordered","Problem Solving":"puzzle",
"Professionalism":"briefcase","Public Speaking":"mic","Relationship Building":"heart-handshake","Relationship Management":"heart-handshake",
"Reliability":"shield-check","Resilience":"shield","Resourcefulness":"wrench","Self Awareness":"scan-face","Social Skills":"messages-square",
"Stakeholder Management":"users","Strategic Planning":"map","Strategic Thinking":"compass","Stress Management":"heart-pulse",
"Team Building":"users-round","Team Leadership":"users","Team Management":"users","Teamwork":"users-round","Teamwork skills":"users-round",
"Time Management":"clock","Time management skills":"clock","Training":"graduation-cap","Vendor Management":"store",
"Verbal Communication":"message-circle","Verbal Communication Skills":"message-circle","Workplace Communication":"message-square-text",
"Written Communication":"pen-line","Written Communication Skills":"pen-line","Work Ethic":"medal",
}

_SOFT = {k.casefold(): v for k, v in SOFT_ICONS.items()}

def icon_url(skill):
    ic = _SOFT.get(skill.casefold())
    if ic:
        return f"{API}lucide/{ic}.svg"
    return enrich(skill)["logo_url"]          # None when nothing matched

def download_svgs(urls, out_dir="icons"):
    """Fetch each distinct icon once (40 per request, polite pauses) and save as SVG files."""
    need = {}
    for u in urls:
        prefix, fn = u[len(API):].split("/")
        need.setdefault(prefix, set()).add(fn[:-4])
    def get(url):
        for t in range(5):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 skills-icon-downloader"})
                with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read())
            except Exception as ex:
                print("retry", t, ex); time.sleep(5 * (t + 1))
        raise SystemExit("download failed: " + url)
    saved = 0
    for prefix, names in sorted(need.items()):
        names = sorted(names); os.makedirs(f"{out_dir}/{prefix}", exist_ok=True)
        for i in range(0, len(names), 40):
            chunk = names[i:i + 40]
            d = get(f"{API}{prefix}.json?icons=" + urllib.parse.quote(",".join(chunk), safe=","))
            W, H = d.get("width", 16), d.get("height", 16)
            icons_, aliases = d.get("icons", {}), d.get("aliases", {})
            for n in chunk:
                a = icons_.get(n)
                if a is None and n in aliases:
                    a = dict(icons_.get(aliases[n]["parent"], {}), **{k: v for k, v in aliases[n].items() if k != "parent"})
                if not a or "body" not in a:
                    print("not found:", prefix, n); continue
                w, h = a.get("width", W), a.get("height", H)
                svg = f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{a["body"]}</svg>'
                open(f"{out_dir}/{prefix}/{n}.svg", "w", encoding="utf-8").write(svg); saved += 1
            time.sleep(0.7)
        print(prefix, len(names), "icons done")
    return saved

if __name__ == "__main__":
    import urllib.parse
    ap = argparse.ArgumentParser()
    ap.add_argument("input"); ap.add_argument("output")
    ap.add_argument("--local", action="store_true", help="download the SVGs and use local paths instead of Iconify URLs")
    ap.add_argument("--base-url", help="write icon links as <base-url><pack>/<name>.svg (where you host the SVGs)")
    a = ap.parse_args()
    if a.local and a.base_url:
        ap.error("use either --local or --base-url, not both")
    skills = json.load(open(a.input, encoding="utf-8"))
    urls = [icon_url(s) for s in skills]
    if a.local:
        print("downloading", len({u for u in urls if u}), "distinct icons ...")
        download_svgs({u for u in urls if u})
        urls = [u.replace(API, "icons/") if u else None for u in urls]
    if a.base_url:
        base = a.base_url if a.base_url.endswith("/") else a.base_url + "/"
        urls = [base + u[len(API):] if u else None for u in urls]
    out = [{"skill": s, "icon": u} for s, u in zip(skills, urls)]
    json.dump(out, open(a.output, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    n = sum(u is None for u in urls)
    print(f"{len(out)} skills written to {a.output}: {len(out) - n} with icon, {n} null")
