#!/usr/bin/env python3
"""Turn the canvas artboards (Main.dc.html, Schools.dc.html) into a plain static website.

Usage: python3 build.py <project_dir> <assets_map.json> <out_dir>
"""
import json, os, re, shutil, sys

SRC, MAPFILE, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
ASSETS = json.load(open(MAPFILE))           # blob id -> local file path
ACCENT = "#FFD23F"
SPEED = 40                                   # px per second, same default as the canvas
SITE_URL = "https://bootcamp.kualalumpurdebate.com"

os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
blob_names = {}
for bid, path in ASSETS.items():
    name = os.path.basename(path)
    shutil.copy(path, os.path.join(OUT, "assets", name))
    blob_names[bid] = "assets/" + name


def split_dc(text):
    head = re.search(r"<helmet>(.*?)</helmet>", text, re.S).group(1)
    body = re.search(r"</helmet>(.*?)</x-dc>", text, re.S).group(1)
    script = re.search(r'<script type="text/x-dc"[^>]*>(.*?)</script>', text, re.S).group(1)
    title = re.search(r"<title>(.*?)</title>", text, re.S).group(1)
    return title, head, body, script


def fix_common(html, page_links):
    html = html.replace("{{accent}}", ACCENT)
    html = re.sub(r"/_blob/([0-9a-f]{32})", lambda m: blob_names[m.group(1)], html)
    for a, b in page_links.items():
        html = html.replace(f'href="{a}"', f'href="{b}"')
    html = re.sub(r'\s+hint-[a-z-]+="[^"]*"', "", html)
    return html


def resolve_ifs(block, item):
    """Resolve <sc-if value="{{x.flag}}"> ... </sc-if> using item's flags (no nesting)."""
    def f(m):
        key = m.group(1).split(".")[-1]
        return m.group(2) if item.get(key) else ""
    return re.sub(r'<sc-if value="\{\{\s*([\w.]+)\s*\}\}"[^>]*>(.*?)</sc-if>', f, block, flags=re.S)


def fill(block, var, item):
    block = resolve_ifs(block, item)
    return re.sub(r"\{\{\s*" + var + r"\.(\w+)\s*\}\}", lambda m: str(item.get(m.group(1), "")), block)


def expand_for(html, listname, items, var):
    pat = re.compile(r'<sc-for list="\{\{' + listname + r'\}\}" as="' + var + r'"[^>]*>(.*?)</sc-for>', re.S)
    m = pat.search(html)
    assert m, listname
    out = "".join(fill(m.group(1), var, it) for it in items)
    return html[:m.start()] + out + html[m.end():]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def page(title, desc, head, body, extra_css, js, og_image):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{SITE_URL}/{og_image}">
<meta property="og:type" content="website">
<link rel="icon" type="image/png" href="{blob_names['b8450b7127a77dcde5771c178af9eccf']}">
{head.strip()}
<style>
html{{scroll-behavior:smooth}}
img{{max-width:100%}}
{extra_css}
</style>
</head>
<body>
{body.strip()}
{('<script>' + js + '</script>') if js else ''}
</body>
</html>
"""


# ---------------------------------------------------------------- Main page
title, head, body, script = split_dc(open(os.path.join(SRC, "Main.dc.html"), encoding="utf-8").read())
body = fix_common(body, {"Schools.dc.html": "international-school-package.html"})

# Partners (data parsed from the canvas script)
partners = []
for m in re.finditer(r"\{ name: '([^']*)', role: '([^']*)', logo: '([^']*)'(?:, align: '([^']*)')? \}", script):
    name, role, logo, align = m.groups()
    logo = re.sub(r"/_blob/([0-9a-f]{32})", lambda x: blob_names[x.group(1)], logo)
    partners.append(dict(name=esc(name), role=esc(role), logo=logo, logoAlign=align or "flex-start",
                         hasLogo=bool(logo), noLogo=not logo, logoLabel=esc("[" + name + " logo]")))
half = []
while len(half) < 8:
    half += partners
body = expand_for(body, "partners", partners, "p")
body = expand_for(body, "marquee", half + half, "p")
body = body.replace("{{marqueeDuration}}", f"{max(8, round(len(half) * 320 / SPEED))}s")

# Endorsers
if "[1, 2, 3, 4, 5, 6].map" in script:
    endorsers = [dict(name=f"[Endorser {i}]", title="[Title, organisation]", photo="") for i in range(1, 7)]
else:
    endorsers = [dict(name=a, title=b, photo=c) for a, b, c in
                 re.findall(r"\{ name: '([^']*)', title: '([^']*)', photo: '([^']*)' \}", script)]
for e in endorsers:
    e["photo"] = re.sub(r"/_blob/([0-9a-f]{32})", lambda x: blob_names[x.group(1)], e["photo"])
    e.update(hasPhoto=bool(e["photo"]), noPhoto=not e["photo"], name=esc(e["name"]), title=esc(e["title"]))
ehalf = []
while len(ehalf) < 10:
    ehalf += endorsers
if "{{endorsers}}" in body:  # the strip can be switched off on the canvas
    body = expand_for(body, "endorsers", endorsers, "e")
    body = expand_for(body, "endorserLoop", ehalf + ehalf, "e")
    body = body.replace("{{endorserDuration}}", f"{max(8, round(len(ehalf) * 200 / SPEED))}s")

# Leads slider
lead_names = re.findall(r"'([^']*)'", re.search(r"const leadNames = \[(.*?)\];", script).group(1))
tab_base = re.search(r'const tabBase = "([^"]*)"', script).group(1)
ON = "background: #121633; color: #FFFFFF; border: 1.5px solid #121633"
OFF = "background: #FFFFFF; color: #344596; border: 1.5px solid #D6DBF0"
tabs = "".join(
    f'<button type="button" class="kd-lead-tab" data-lead-tab="{i}" aria-pressed="{"true" if i == 0 else "false"}" '
    f'style="{tab_base}{ON if i == 0 else OFF}">{esc(n)}</button>'
    for i, n in enumerate(lead_names))
body = re.sub(r'<sc-for list="\{\{leadTabs\}\}".*?</sc-for>', tabs, body, flags=re.S)
n_leads = len(lead_names)
body = body.replace("{{leadCounter}}", f'<span id="lead-counter">01 / {n_leads:02d}</span>')
body = body.replace('onClick="{{prevLead}}"', 'data-lead-nav="prev"').replace('onClick="{{nextLead}}"', 'data-lead-nav="next"')
for i in range(n_leads):
    body = re.sub(r'<sc-if value="\{\{showLead' + str(i) + r'\}\}"[^>]*>(.*?)</sc-if>',
                  lambda m: f'<div class="kd-lead" data-lead="{i}"{"" if i == 0 else " hidden"}>{m.group(1)}</div>',
                  body, flags=re.S)

# Schedule dropdowns (Day 1 open, others closed on phones)
for i in range(3):
    o = i == 0
    body = body.replace(f"{{{{day{i}Display}}}}", "flex" if o else "none")
    body = body.replace(f"{{{{day{i}Expanded}}}}", "true" if o else "false")
    body = body.replace(f"{{{{day{i}Rotate}}}}", "180deg" if o else "0deg")
    body = body.replace(f'onClick="{{{{toggleDay{i}}}}}"', f'data-day-toggle="{i}"')
cnt = 0
def tag_list(m):
    global cnt
    r = m.group(0).replace('class="kd-day-list"', f'class="kd-day-list" data-day-list="{cnt}"'); cnt += 1; return r
body = re.sub(r'<ol class="kd-day-list"', tag_list, body)

# Stripe pricing table (website only; the canvas shows a placeholder). The publishable key is meant to be public.
STRIPE_TABLE_ID = "prctbl_1UVuKKPwAVpYLYZakzp7rGNS"
STRIPE_PK = "pk_live_51UVkacPwAVpYLYZa4HWnOyZseXLApwT7yGTsVIyuMVqDLfXrJ10x12S7rUCvAVsdlgUqeL5PampTEt8mc9jnOd8C00AfVamsSs"
stripe_html = ('<div class="kd-stripe" style="border-radius: 20px; background: #FFFFFF; padding: clamp(8px, 2vw, 24px)">'
               '<script async src="https://js.stripe.com/v3/pricing-table.js"></script>'
               f'<stripe-pricing-table pricing-table-id="{STRIPE_TABLE_ID}" publishable-key="{STRIPE_PK}"></stripe-pricing-table>'
               '</div>')
body, n_slots = re.subn(r'<div data-stripe-slot="pricing-table"[^>]*>.*?</div>', stripe_html, body, count=1, flags=re.S)
assert n_slots == 1, "Stripe placeholder not found on the canvas page"

left = re.findall(r"\{\{[^}]*\}\}|<sc-|onClick=", body)
assert not left, left[:5]

main_js = r"""
(function(){
  var leads=[].slice.call(document.querySelectorAll('.kd-lead'));
  var tabs=[].slice.call(document.querySelectorAll('.kd-lead-tab'));
  var counter=document.getElementById('lead-counter');
  var ON='background: #121633; color: #FFFFFF; border: 1.5px solid #121633', OFF='background: #FFFFFF; color: #344596; border: 1.5px solid #D6DBF0';
  var cur=0, n=leads.length;
  function pad(x){return (x<10?'0':'')+x;}
  function show(i){
    cur=((i%n)+n)%n;
    leads.forEach(function(el,k){el.hidden=k!==cur;});
    tabs.forEach(function(t,k){
      t.setAttribute('aria-pressed',k===cur?'true':'false');
      t.style.cssText=t.style.cssText.replace(/background:[^;]*;\s*color:[^;]*;\s*border:[^;]*(;|$)/,'')+';'+(k===cur?ON:OFF);
    });
    if(counter) counter.textContent=pad(cur+1)+' / '+pad(n);
  }
  tabs.forEach(function(t){t.addEventListener('click',function(){show(+t.getAttribute('data-lead-tab'));});});
  [].forEach.call(document.querySelectorAll('[data-lead-nav]'),function(b){
    b.addEventListener('click',function(){show(cur+(b.getAttribute('data-lead-nav')==='next'?1:-1));});
  });
  [].forEach.call(document.querySelectorAll('[data-day-toggle]'),function(b){
    b.addEventListener('click',function(){
      var i=b.getAttribute('data-day-toggle');
      var list=document.querySelector('[data-day-list="'+i+'"]');
      var open=b.getAttribute('aria-expanded')!=='true';
      b.setAttribute('aria-expanded',open?'true':'false');
      list.style.display=open?'flex':'none';
      var chev=b.querySelector('span'); if(chev) chev.style.transform='rotate('+(open?180:0)+'deg)';
    });
  });
})();
"""
desc = ("KL Debate Bootcamp, December 2026 at TEDOH, Kuala Lumpur: three days of public speaking, "
        "critical thinking and debate for students aged 7 to 18.")
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(
    page(title, desc, head, body, "", main_js, blob_names["b7ccdbf2242079eb873744563a7671cf"]))

# ---------------------------------------------------------------- Schools page
title, head, body, script = split_dc(open(os.path.join(SRC, "Schools.dc.html"), encoding="utf-8").read())
body = fix_common(body, {"Main.dc.html": "index.html"})
left = re.findall(r"\{\{[^}]*\}\}|<sc-|onClick=", body)
assert not left, left[:5]
desc = ("The International School Package: USD 350 per student for every 10 students your school enrols "
        "in the KL Debate Bootcamp, December 2026, Kuala Lumpur.")
open(os.path.join(OUT, "international-school-package.html"), "w", encoding="utf-8").write(
    page(title + " | KL Debate Bootcamp", desc, head, body, "", "", blob_names["b7ccdbf2242079eb873744563a7671cf"]))
print("built", sorted(os.listdir(OUT)), sorted(os.listdir(os.path.join(OUT, "assets"))))
