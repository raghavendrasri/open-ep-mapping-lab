"""Build learning-hub/index.html from the author's original page (made with Muse).

The original is kept unchanged in learning-hub/source/. This script applies the edits needed to meet CLAUDE.md:
self-hosted fonts instead of Google Fonts, an original SVG drawing instead of the embedded raster image,
description instead of ablation advice, citations for product facts and numbers (with "unverified" tags where no
independent source was found), and a reference list built from references.bib. Every replacement must match
exactly once, so a change to the original page fails loudly instead of being skipped.

Run from the repository root:  python tools/build_learning_hub.py
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "learning-hub" / "source" / "Electrophysiology_Mapping_System.html"
HERO = ROOT / "learning-hub" / "source" / "hero.svg"
OUT = ROOT / "learning-hub" / "index.html"

# References cited on the page, in the order they are listed. Every key must be in references.bib.
REFS = ["gepstein1997", "anter2015", "anter2015orion", "sultan2019", "masuda2024", "sarkozy2022", "masse2016",
        "deno2017", "magtibay2019", "abeln2021", "rottner2021", "pope2022", "marchlinski2000", "teijeira2018",
        "koawing2015", "aziz2019", "stevenson1993"]


def bib_entries() -> dict[str, dict[str, str]]:
    text = (ROOT / "references.bib").read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"@\w+\{([^,]+),(.*?)\n\}", text, re.S):
        fields = dict(re.findall(r"^\s*(\w+)\s*=\s*\{(.*)\},?\s*$", m.group(2), re.M))
        out[m.group(1)] = fields
    return out


def clean(s: str) -> str:
    s = re.sub(r"\{\\[\"'`^~]\{?(\w)\}?\}", lambda m: m.group(1), s)   # {\'e} -> e (accents dropped, plain text)
    s = s.replace("\\&", "&").replace("{", "").replace("}", "")
    return s


def year_labels(entries) -> dict[str, str]:
    """Year shown for each reference: 2015a and 2015b when the same first author has two papers in one year."""
    base = {k: (clean(entries[k]["author"].split(" and ")[0].split(",")[0]).strip(), entries[k]["year"]) for k in REFS}
    out = {}
    for k in REFS:
        same = [j for j in REFS if base[j] == base[k]]
        out[k] = base[k][1] + ("abcdefgh"[same.index(k)] if len(same) > 1 else "")
    return out


def cite(key: str, entries, years) -> str:
    first = clean(entries[key]["author"].split(" and ")[0].split(",")[0]).strip()
    return f'<a class="cite" href="#ref-{key}">{first} {years[key]}</a>'


UNV = '<span class="unv" title="No independent source found yet; see the pull request and errata.json">unverified</span>'


def main(out_path: Path = OUT) -> int:
    entries = bib_entries()
    missing = [k for k in REFS if k not in entries]
    if missing:
        print("missing from references.bib:", missing)
        return 1
    years = year_labels(entries)
    C = {k: cite(k, entries, years) for k in REFS}
    s = SRC.read_text(encoding="utf-8")
    hero = HERO.read_text(encoding="utf-8")
    edits: list[tuple[str, str]] = []

    def E(old: str, new: str) -> None:
        edits.append((old, new))

    # ---------------------------------------------------------------- fonts: self-hosted, no network requests
    E('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
      '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
      '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Serif:wght@500;600;700&display=swap" rel="stylesheet">\n<style>\n',
      "<style>\n" + "".join(
          f'@font-face{{font-family:"IBM Plex {fam.title()}";font-style:{st};font-weight:{w};font-display:swap;'
          f'src:url("../vendor/fonts/ibm-plex/ibm-plex-{fam}-latin-{w}-{st}.woff2") format("woff2")}}\n'
          for fam, w, st in [("sans", 400, "normal"), ("sans", 400, "italic"), ("sans", 500, "normal"),
                             ("sans", 600, "normal"), ("serif", 400, "normal"), ("serif", 500, "normal"),
                             ("serif", 600, "normal"), ("mono", 400, "normal"), ("mono", 500, "normal"),
                             ("mono", 600, "normal")]))
    # ---------------------------------------------------------------- icon & SEO metadata
    hub_url = "https://openepengineering.org/learning-hub/index.html"
    hub_desc = (
        "Interactive guide to cardiac electrophysiology (EP) mapping systems: activation map simulator, "
        "lab workflow, platform comparisons (CARTO 3, EnSite X, OPAL HDx, KODEX-EPD, AcQMap) and electrogram lab."
    )
    hub_desc_short = (
        "Interactive guide to cardiac electrophysiology mapping systems: live activation simulator, "
        "lab workflow, platform comparisons, electrogram lab and glossary."
    )
    og_img = "https://openepengineering.org/assets/logo/og-card.png"
    hub_jsonld = (
        '<script type="application/ld+json">\n'
        '{\n'
        '  "@context": "https://schema.org",\n'
        '  "@graph": [\n'
        '    {\n'
        '      "@type": "LearningResource",\n'
        '      "name": "Electrophysiology Mapping System — Learning Hub & Explorer",\n'
        f'      "description": "{hub_desc_short}",\n'
        f'      "url": "{hub_url}",\n'
        '      "inLanguage": "en",\n'
        '      "isAccessibleForFree": true,\n'
        '      "license": "https://creativecommons.org/licenses/by/4.0/",\n'
        '      "learningResourceType": "Interactive simulation",\n'
        '      "isPartOf": {"@type": "Course", "name": "Open EP Mapping Lab", "url": "https://openepengineering.org/"}\n'
        '    },\n'
        '    {\n'
        '      "@type": "BreadcrumbList",\n'
        '      "itemListElement": [\n'
        '        {"@type": "ListItem", "position": 1, "name": "Open EP Mapping Lab", "item": "https://openepengineering.org/"},\n'
        f'        {{"@type": "ListItem", "position": 2, "name": "Learning Hub", "item": "{hub_url}"}}\n'
        '      ]\n'
        '    }\n'
        '  ]\n'
        '}\n'
        '</script>'
    )
    E('<link rel="icon" href="data:," />',
      '<link rel="icon" type="image/png" href="../favicon.png" />\n'
      f'<meta name="description" content="{hub_desc_short}" />\n'
      '<meta name="robots" content="index, follow, max-image-preview:large" />\n'
      f'<link rel="canonical" href="{hub_url}" />\n'
      '<meta property="og:type" content="website" />\n'
      '<meta property="og:site_name" content="Open EP Mapping Lab" />\n'
      '<meta property="og:title" content="EP Mapping System — Interactive Learning Hub &amp; Explorer" />\n'
      f'<meta property="og:description" content="{hub_desc}" />\n'
      f'<meta property="og:url" content="{hub_url}" />\n'
      f'<meta property="og:image" content="{og_img}" />\n'
      '<meta name="twitter:card" content="summary_large_image" />\n'
      '<meta name="twitter:title" content="EP Mapping System — Interactive Learning Hub &amp; Explorer" />\n'
      f'<meta name="twitter:description" content="{hub_desc_short}" />\n'
      f'<meta name="twitter:image" content="{og_img}" />\n'
      f'{hub_jsonld}')
    E("footer a{color:var(--ink2)}",
      "footer a{color:var(--ink2)}\n"
      ".cite{font-size:.8em;color:var(--teal);text-decoration:none;border-bottom:1px dotted currentColor;white-space:nowrap}\n"
      ".hero .cite,.sim .cite{color:#5eead4}\n"
      ".unv{display:inline-block;font-family:var(--font-mono);font-size:.6rem;letter-spacing:.06em;text-transform:uppercase;"
      "color:var(--amber);border:1px solid currentColor;border-radius:4px;padding:0 4px;margin-left:3px;vertical-align:middle;line-height:1.5}\n"
      ".status{background:#fff7e6;color:#5c3b00;border-bottom:1px solid #f0d9a8;font-size:.86rem;padding:9px 0}\n"
      ".status a{color:inherit}\n"
      "@media (prefers-color-scheme: dark){.status{background:#2a2110;color:#f3dfb4;border-color:#4a3a1a}}\n"
      ".hero-img svg{position:absolute;inset:0;width:100%;height:100%;display:block}\n"
      ".tab-pane[hidden]{display:none!important}\n"
      ".refs{margin:10px 0 0 18px;padding:0}.refs li{margin:5px 0}")

    # ---------------------------------------------------------------- navigation and status
    E('      <a href="#simulator">Simulator</a>',
      '      <a href="../index.html">Course home</a>\n      <a href="#simulator">Simulator</a>')
    E('</nav>\n',
      '</nav>\n<div class="status" role="note"><div class="wrap"><b>Draft · pending clinical review.</b> Education only: '
      'not for diagnosis, treatment or any clinical decision. Facts carry a citation (listed at the bottom); items marked '
      f'{UNV} have no independent source yet. Part of the <a href="../index.html">Open EP Mapping Lab</a> course.</div></div>\n')

    # ---------------------------------------------------------------- hero
    E("into a live, colour-coded 3D map — so a clinician can find exactly where an abnormal rhythm starts, how it travels, and where to treat it.",
      "into a live, colour-coded 3D map that shows where an abnormal rhythm starts and how it travels.")
    E("<span>Catheter navigation and ablation, often with little or no X-ray</span>",
      f"<span>Catheter navigation and ablation, locating catheters without X-ray {C['gepstein1997']}</span>")
    E("<b>What it treats</b><span>AF, atrial flutter, SVT, PVCs and ventricular tachycardia</span>",
      "<b>Where it is used</b><span>Procedures for AF, atrial flutter, SVT, PVCs and ventricular tachycardia</span>")
    i = s.index('<img src="data:image/webp;base64,')
    j = s.index("/>", i) + 2
    E(s[i:j], hero)
    E("<figcaption>ILLUSTRATION — ACTIVATION MAP + MAPPING CATHETER</figcaption>",
      "<figcaption>SCHEMATIC — ACTIVATION MAP + MAPPING CATHETER (ORIGINAL DRAWING)</figcaption>")

    # ---------------------------------------------------------------- five links
    E('<span class="n">05 · TREAT</span><h3>Ablation target</h3><p>The map pinpoints the source or circuit. An ablation catheter delivers RF, cryo or pulsed-field energy there, and the map confirms the result.</p>',
      '<span class="n">05 · GUIDE</span><h3>Ablation guidance</h3><p>The map shows where the source or circuit lies. The clinical team uses it to guide ablation with RF, cryo or pulsed-field energy, and can map again to check the result.</p>')

    # ---------------------------------------------------------------- simulator (initial text; the script sets the rest)
    focal_look = "Find the earliest (red) point first: in a focal rhythm it marks where activation begins, and everything else is the wave spreading from it."
    E('<p id="simLook">Find the earliest (red) point first — that is the source. Everything else is just the wave leaving it. Ablation targets the red spot itself, not the tissue it spreads into.</p>',
      f'<p id="simLook">{focal_look}</p>')
    E('<span class="val" id="simStat1">Cycle length ≈ 300 ms</span><br><span id="simStat2">A single source drives the whole chamber, so one well-placed lesion can end it.</span>',
      '<span class="val" id="simStat1">Cycle length in this simulation ≈ 300 ms (illustrative)</span><br><span id="simStat2">In this model a single source drives the whole chamber.</span>')
    E("look:'Find the earliest (red) point first — that is the source. Everything else is just the wave leaving it. Ablation targets the red spot itself, not the tissue it spreads into.',stat1:'Cycle length ≈ 300 ms',stat2:'A single source drives the whole chamber, so one well-placed lesion can end it.'",
      f"look:'{focal_look}',stat1:'Cycle length in this simulation ≈ 300 ms (illustrative)',stat2:'In this model a single source drives the whole chamber.'")
    E("That seam, plus a full rainbow around the loop, is the signature of re-entry. Treatment is a line of ablation across the narrow isthmus the loop must pass through.',stat1:'Cycle length ≈ 240 ms'",
      "That seam, plus a full rainbow around the loop, is the signature of re-entry. Mapping tries to find the narrow isthmus the loop must pass through.',stat1:'Cycle length in this simulation ≈ 240 ms (illustrative)'")
    E("stat1:'Cycle length ≈ 800 ms (75 bpm)'", "stat1:'Cycle length in this simulation ≈ 800 ms, 75 beats/min (illustrative)'")
    E("No single LAT map can capture it, which is why AF work leans on voltage maps, vein potentials and anatomy instead.',look:'There is no stable “earliest point” to chase — watch how the colours refuse to repeat. This is exactly why point-by-point activation mapping struggles in AF, and why pulmonary vein isolation is an anatomical strategy.',stat1:'Local cycle lengths vary, ~120–180 ms',stat2:'Chaotic and non-repeating: substrate and anatomy maps take over from LAT.'",
      "No single LAT map can capture it.',look:'There is no stable “earliest point” to chase — watch how the colours refuse to repeat. This is why point-by-point activation mapping struggles in AF.',stat1:'Local cycle lengths vary from place to place (illustrative)',stat2:'Chaotic and non-repeating in this model.'")
    E("look:'Scar itself is electrically silent — the target in scar-related VT is usually the border zone and the narrow channels of surviving tissue inside the scar, where re-entry loops hide.',stat1:'Common bipolar threshold: < 0.5 mV = dense scar',stat2:'0.5–1.5 mV is usually read as border zone; above that, healthy tissue. Thresholds vary by chamber and lab.'",
      f"look:'Dense scar records almost no local signal. The border zone and the surviving channel through the scar are what a voltage map helps to show.',stat1:'Classic ventricular bipolar cutoffs: below 0.5 mV dense scar, above 1.5 mV normal',stat2:'From one early study {C['marchlinski2000']}; cutoffs depend on chamber, catheter and contact (course module m23).'")
    for el in ("simLook", "simStat1", "simStat2"):
        E(f"document.getElementById('{el}').textContent=r.", f"document.getElementById('{el}').innerHTML=r.")

    # ---------------------------------------------------------------- workflow
    E("<b>Density matters:</b> a modern high-density map can hold thousands to tens of thousands of points",
      f"<b>Density matters:</b> high-density maps in published studies held thousands of points {C['aziz2019']} {C['masuda2024']}")
    E("{t:'Interpret & target',d:'The electrophysiologist reads the finished map: find the focal source, trace the re-entry loop, or map the scar channels — then cross-checks with entrainment or pace mapping before committing to a lesion.'",
      "{t:'Interpret the map',d:'The electrophysiologist reads the finished map — a focal source, a re-entry loop, or channels through scar — and may cross-check it with pacing tests such as entrainment or pace mapping (course module m11).'")
    E("'<b>Rule of the lab:</b> never ablate on colour alone — confirm with the signals'",
      "'<b>Why it matters:</b> a colour map is only as good as the electrograms behind it (course module m22)'")
    E("{t:'Ablate & prove the endpoint',d:'The ablation catheter delivers energy at the target — radiofrequency heat, cryo freezing, or pulsed-field energy. Lesions are tagged on the map. The case ends only when the endpoint is demonstrated: veins isolated, a line proven blocked, or the arrhythmia no longer inducible.',pts:['<b>Mapping system’s job:</b> tag each lesion with force, power and time; re-map to prove the result','<b>Endpoint examples:</b> entrance + exit block for pulmonary vein isolation']}",
      f"{{t:'Ablate & re-map',d:'The ablation catheter delivers energy — radiofrequency heat, cryo freezing, or pulsed-field energy. Lesions are tagged on the map, and the team can map again to check the result.',pts:['<b>Mapping system’s job:</b> tag each lesion with force, power and time; re-map to check the result','<b>Example:</b> after pulmonary vein isolation, vein potentials can be checked with a circular or basket catheter {C['anter2015orion']}']}}")

    # ---------------------------------------------------------------- systems explorer
    E("<p>Five platforms dominate modern EP labs. They all build the same kinds of maps — what differs is the localisation physics, the signature catheter, and the philosophy: closed and integrated, open to other brands' catheters, or built for maximum point density.</p>",
      "<p>This explorer compares five platforms described in published studies. They all build the same kinds of maps — what differs is the localisation physics, the signature catheter, and the design philosophy: closed and integrated, open to other brands' catheters, or built for maximum point density.</p>")
    E("desc:'The most widely installed platform and the reference point others are compared against. CARTO 3 combines a magnetic sensor in the catheter tip with current-based localisation, and wraps mapping, contact-force ablation, lesion tagging and intracardiac echo into one tightly integrated ecosystem.',loc:'Hybrid — magnetic location pad under the table + impedance/current-based tracking',cat:'OCTARAY (48 electrodes, 8 splines) and PentaRay (20 electrodes, 5 splines) multi-spline catheters',sig:'CONFIDENSE continuous mapping; VISITAG lesion tagging; CARTOSOUND ICE integration',best:'Integrated AF and VT workflows where mapping, ablation and imaging stay in one family'",
      f"desc:'CARTO 3 locates the catheter tip with a magnetic sensor (the principle was described by Gepstein and colleagues {C['gepstein1997']}) combined with current-based localisation {UNV}, and wraps mapping, contact-force ablation, lesion tagging and intracardiac echo into one integrated system {UNV}.',loc:'Hybrid — magnetic location pad under the table + impedance/current-based tracking {UNV}',cat:'OCTARAY (48 electrodes on 8 splines) {C['masuda2024']} {C['sarkozy2022']} and PentaRay (20 electrodes, 5 splines) {UNV} multi-spline catheters',sig:'CONFIDENSE continuous mapping; VISITAG lesion tagging; CARTOSOUND ICE integration {UNV}',best:'Integrated AF and VT workflows where mapping, ablation and imaging stay in one family {UNV}'")
    E("desc:'Abbott’s current platform, built around an open architecture: it can visualise catheters from other manufacturers, not just Abbott’s. Its signature idea is omnipolar technology — using the HD Grid’s two-axis electrode array to compute the electrogram’s true maximum amplitude and wavefront direction, removing the classic bipolar blind spot where a wave travelling along a bipole reads falsely small.',loc:'Hybrid — impedance-based VoXel mode + magnetic sensor-enabled tracking',cat:'Advisor HD Grid — 4 × 4 paddle, 16 electrodes, purpose-built for omnipolar acquisition',sig:'EnSite Omnipolar Technology (OT); Near Field / peak-frequency tools for picking the true near-field signal',best:'Labs that value catheter choice, and voltage mapping where wavefront direction would otherwise distort the picture'",
      f"desc:'Abbott’s platform is described as an open architecture that can show other manufacturers’ catheters {UNV}. Its signature idea is omnipolar technology: using a grid of electrodes to estimate the electrogram’s amplitude and the wavefront direction largely independently of how the catheter is oriented {C['masse2016']} {C['deno2017']}, reducing the bipolar blind spot where a wave crossing at right angles to a bipole reads falsely small (course module m23).',loc:'Hybrid — impedance-based VoXel mode + magnetic sensor-enabled tracking {UNV}',cat:'Advisor HD Grid — 4 × 4 paddle, 16 electrodes {UNV}, used for omnipolar acquisition {C['magtibay2019']}',sig:'EnSite Omnipolar Technology (OT); Near Field / peak-frequency tools {UNV}',best:'Voltage and activation mapping where wavefront direction would otherwise distort the picture {C['magtibay2019']}'")
    E("desc:'Boston Scientific’s mapping platform — renamed from Rhythmia HDx to OPAL HDx — was built for one thing above all: density. Its Orion mini-basket carries 64 very small electrodes, and the system automatically accepts or rejects beats against stability criteria, assembling ultra-high-density maps with minimal manual point-picking.',loc:'Hybrid — magnetic + impedance localisation',cat:'IntellaMap Orion — expandable mini-basket, 64 electrodes on 8 splines',sig:'Ultra-high-density automated mapping; LUMIPOINT tools that highlight late and fragmented activity within a chosen window',best:'Complex re-do AF cases, atypical flutters and scar VT where fine detail decides the target'",
      f"desc:'Boston Scientific’s mapping platform (Rhythmia; the newer name OPAL HDx {UNV}) was built around density. Its Orion mini-basket carries 64 small electrodes {C['anter2015orion']} and is paired with an automated mapping system {C['sultan2019']} that accepts or rejects beats against stability criteria {UNV}, assembling high-density maps with little manual point-picking.',loc:'Hybrid — magnetic + impedance localisation {UNV}',cat:'IntellaMap Orion — expandable mini-basket, 64 electrodes {C['anter2015orion']} on 8 splines {UNV}',sig:'High-density automated mapping {C['sultan2019']}; LUMIPOINT tools that highlight late and fragmented activity within a chosen window {UNV}',best:'Complex atrial and ventricular maps where fine detail matters {UNV}'")
    E("desc:'A different physical principle altogether: dielectric sensing. Electrodes measure how the surrounding tissue and blood alter an applied field, letting KODEX-EPD reconstruct detailed anatomy in real time without a magnetic field generator — and it works with validated catheters from any manufacturer. NICE’s overview notes it can provide imaging within minutes and is aimed at reducing X-ray use.',loc:'Dielectric sensing — no magnetic generator; open platform for validated catheters',cat:'No proprietary mapping catheter — uses the lab’s existing validated EP catheters',sig:'Real-time high-definition anatomy; occlusion visualisation tools for cryoballoon procedures',best:'Cryoballoon AF ablation and labs wanting fast anatomy without importing a CT'",
      f"desc:'A different physical principle: dielectric sensing. Electrical fields distinguish structures by their conductivity and permittivity, so the system can image anatomy without fluoroscopy {C['abeln2021']}. In 65 patients having cryoballoon ablation, its pulmonary vein measurements differed from angiography by about 1 mm on average {C['rottner2021']}. It is described as working without a magnetic field generator and with validated catheters from other manufacturers {UNV}.',loc:'Dielectric sensing {C['abeln2021']}; open platform for validated catheters {UNV}',cat:'No proprietary mapping catheter — uses the lab’s existing validated EP catheters {UNV}',sig:'High-resolution anatomy; pulmonary vein occlusion assessment during cryoballoon ablation {C['abeln2021']}',best:'Cryoballoon AF ablation {C['rottner2021']}'")
    E("{name:'AcQMap',maker:'Acutus Medical',",
      "{name:'AcQMap',maker:'Acutus Medical (mapping platform sold to EnChannel Medical in 2025)',")
    # ---------------------------------------------------------------- crawlable tab panels: render all panels in DOM
    E("  function show(i){ var s=steps[i];\n"
      "    det.innerHTML='<p class=\"kicker\" style=\"margin-bottom:6px\">Stage 0'+(i+1)+' of 06</p><h3>'+s.t+'</h3><p>'+s.d+'</p><ul>'+s.pts.map(function(p){return '<li>'+p+'</li>'}).join('')+'</ul>';\n"
      "  }\n"
      "  show(0);",
      "  det.innerHTML=steps.map(function(s,i){ return '<div class=\"tab-pane\"'+(i===0?'':' hidden')+'><p class=\"kicker\" style=\"margin-bottom:6px\">Stage 0'+(i+1)+' of 06</p><h3>'+s.t+'</h3><p>'+s.d+'</p><ul>'+s.pts.map(function(p){return '<li>'+p+'</li>'}).join('')+'</ul></div>'; }).join('');\n"
      "  function show(i){ det.querySelectorAll('.tab-pane').forEach(function(p,idx){ p.hidden=idx!==i; }); }\n"
      "  show(0);")
    E("  function show(i){ var s=systems[i];\n"
      "    panel.innerHTML='<div class=\"panel-grid\"><div><p class=\"maker\">'+s.maker+'</p><h3>'+s.name+'</h3><p>'+s.desc+'</p><div class=\"tag-row\">'+s.tags.map(function(t){return '<span class=\"tag\">'+t+'</span>'}).join('')+'</div></div>'\n"
      "    +'<div><ul class=\"spec-list\"><li><b>Localisation</b>'+s.loc+'</li><li><b>Signature catheter</b>'+s.cat+'</li><li><b>Signature software</b>'+s.sig+'</li><li><b>Best known for</b>'+s.best+'</li></ul></div></div>';\n"
      "  }\n"
      "  show(0);",
      "  panel.innerHTML=systems.map(function(s,i){ return '<div class=\"panel-grid tab-pane\"'+(i===0?'':' hidden')+'><div><p class=\"maker\">'+s.maker+'</p><h3>'+s.name+'</h3><p>'+s.desc+'</p><div class=\"tag-row\">'+s.tags.map(function(t){return '<span class=\"tag\">'+t+'</span>'}).join('')+'</div></div>'\n"
      "    +'<div><ul class=\"spec-list\"><li><b>Localisation</b>'+s.loc+'</li><li><b>Signature catheter</b>'+s.cat+'</li><li><b>Signature software</b>'+s.sig+'</li><li><b>Best known for</b>'+s.best+'</li></ul></div></div>'; }).join('');\n"
      "  function show(i){ panel.querySelectorAll('.tab-pane').forEach(function(p,idx){ p.hidden=idx!==i; }); }\n"
      "  show(0);")
    E("  function show(i){ var m=modes[i];\n"
      "    panel.innerHTML='<div class=\"panel-grid\"><div><h3>'+m.name+'</h3><p style=\"font-family:var(--font-serif);font-size:1.08rem;color:var(--ink)\">'+m.q+'</p><p>'+m.d+'</p></div><div><ul class=\"spec-list\"><li><b>Typically used for</b>'+m.ex+'</li></ul></div></div>';\n"
      "  }\n"
      "  show(0);",
      "  panel.innerHTML=modes.map(function(m,i){ return '<div class=\"panel-grid tab-pane\"'+(i===0?'':' hidden')+'><div><h3>'+m.name+'</h3><p style=\"font-family:var(--font-serif);font-size:1.08rem;color:var(--ink)\">'+m.q+'</p><p>'+m.d+'</p></div><div><ul class=\"spec-list\"><li><b>Typically used for</b>'+m.ex+'</li></ul></div></div>'; }).join('');\n"
      "  function show(i){ panel.querySelectorAll('.tab-pane').forEach(function(p,idx){ p.hidden=idx!==i; }); }\n"
      "  show(0);")

    E("desc:'The non-contact outlier. Instead of touching the wall point by point, its balloon catheter floats in the chamber: ultrasound transducers rebuild the anatomy while 48 electrodes sense the chamber’s electrical field, and inverse-solution mathematics reconstructs charge density on the wall — capturing an entire chamber in a single beat.',loc:'Ultrasound-based anatomy + non-contact electrical sensing (inverse solution)',cat:'AcQMap balloon — 48 ultrasound transducers and 48 electrodes on one catheter',sig:'Single-beat, whole-chamber charge-density maps — works even when the rhythm is unstable or non-sustained',best:'Unstable or constantly changing rhythms that point-by-point mapping cannot keep up with'",
      f"desc:'The non-contact outlier. Instead of touching the wall point by point, its balloon catheter floats in the chamber: ultrasound rebuilds the anatomy while electrodes sense the chamber’s electrical field, and an inverse solution reconstructs charge density on the wall, showing whole-chamber activation, including during AF {C['pope2022']}.',loc:'Ultrasound-based anatomy + non-contact electrical sensing (inverse solution) {C['pope2022']}',cat:'AcQMap balloon — 48 ultrasound transducers and 48 electrodes {UNV}',sig:'Whole-chamber charge-density maps {C['pope2022']}; single-beat capture of unstable rhythms {UNV}',best:'Rhythms that change too often for point-by-point mapping, such as AF {C['pope2022']}'")
    E('<tr><th scope="row">CARTO 3</th><td>Magnetic sensor + current-based (impedance) hybrid</td><td>OCTARAY &amp; PentaRay multi-spline</td><td>Integrated ecosystem, contact-force ablation, ICE integration</td></tr>',
      f'<tr><th scope="row">CARTO 3</th><td>Magnetic sensor {C["gepstein1997"]} + current-based (impedance) hybrid {UNV}</td><td>OCTARAY {C["sarkozy2022"]} &amp; PentaRay multi-spline</td><td>Integrated ecosystem, contact-force ablation, ICE integration {UNV}</td></tr>')
    E('<tr><th scope="row">EnSite X</th><td>Impedance (VoXel) + magnetic hybrid, open architecture</td><td>Advisor HD Grid paddle</td><td>Omnipolar mapping — voltage independent of wavefront direction</td></tr>',
      f'<tr><th scope="row">EnSite X</th><td>Impedance (VoXel) + magnetic hybrid, open architecture {UNV}</td><td>Advisor HD Grid paddle {C["magtibay2019"]}</td><td>Omnipolar mapping — voltage much less dependent on wavefront direction {C["deno2017"]}</td></tr>')
    E('<tr><th scope="row">OPAL HDx <span style="color:var(--muted);font-weight:400">(formerly Rhythmia HDx)</span></th><td>Magnetic + impedance hybrid</td><td>IntellaMap Orion mini-basket (64 electrodes)</td><td>Ultra-high-density automated mapping</td></tr>',
      f'<tr><th scope="row">OPAL HDx <span style="color:var(--muted);font-weight:400">(formerly Rhythmia HDx)</span> {UNV}</th><td>Magnetic + impedance hybrid {UNV}</td><td>IntellaMap Orion mini-basket (64 electrodes) {C["anter2015orion"]}</td><td>High-density automated mapping {C["sultan2019"]}</td></tr>')
    E('<tr><th scope="row">KODEX-EPD</th><td>Dielectric sensing — no magnetic field generator</td><td>Works with validated catheters from any maker</td><td>Fast, detailed anatomy imaging, strong for cryoballoon cases</td></tr>',
      f'<tr><th scope="row">KODEX-EPD</th><td>Dielectric sensing {C["abeln2021"]} — no magnetic field generator {UNV}</td><td>Works with validated catheters from other makers {UNV}</td><td>Detailed anatomy imaging; studied in cryoballoon ablation {C["rottner2021"]}</td></tr>')
    E('<tr><th scope="row">AcQMap</th><td>Ultrasound anatomy + non-contact charge-density sensing</td><td>AcQMap balloon (48 ultrasound transducers, 48 electrodes)</td><td>Single-beat, whole-chamber mapping of unstable rhythms</td></tr>',
      f'<tr><th scope="row">AcQMap</th><td>Ultrasound anatomy + non-contact charge-density sensing {C["pope2022"]}</td><td>AcQMap balloon (48 ultrasound transducers, 48 electrodes) {UNV}</td><td>Whole-chamber activation, including during AF {C["pope2022"]}</td></tr>')
    E("Platform names and catheter names are trademarks of their makers. Descriptions are educational summaries — see the sources at the bottom for the manufacturers' own pages.",
      "Platform and catheter names are trademarks of their makers, used here only to identify the products. Facts carry a citation to a published study, listed at the bottom; items marked unverified have none yet. Manufacturer pages are listed for further reading, not as sources.")

    # ---------------------------------------------------------------- map types
    E("Read it with the direction caveat: standard bipolar voltage shrinks when the wavefront runs along the bipole — the problem omnipolar mapping was built to solve.',ex:'Ischaemic and non-ischaemic VT, atrial scar and low-voltage areas in persistent AF'",
      "Read it with the direction caveat: standard bipolar voltage shrinks when the wave travels at right angles to the bipole (course module m23) — the problem omnipolar mapping was built to address.',ex:'Ischaemic and non-ischaemic VT, atrial scar and low-voltage areas in persistent AF'")
    E("the border zone between them is where re-entry circuits for ventricular tachycardia usually live.",
      "the border zone between them is where re-entry circuits for ventricular tachycardia are often described.")
    E("d:'Not a colour map but a pacing test layered on top of one. Pacing from a candidate site: if the paced rhythm matches the tachycardia and the post-pacing interval is within ~30 ms of the cycle length, that site is in or near the circuit. It is the classic cross-check before ablating a flutter or VT isthmus.'",
      f"d:'Not a colour map but a pacing test layered on top of one. Pacing from a candidate site and comparing the paced rhythm and the post-pacing interval with the tachycardia’s cycle length indicates whether the site is in or near the circuit {C['stevenson1993']} (course module m11).'")
    E("Tools such as LUMIPOINT-style illumination surface these signals inside a chosen time window. Targets here are probabilistic, so they are usually combined with voltage and activation data.",
      "Some systems highlight these signals inside a chosen time window. These findings are probabilistic, so they are usually read together with voltage and activation data.")

    # ---------------------------------------------------------------- electrogram lab
    E("a large bipolar electrogram (several mV) with a crisp downstroke.",
      f"a large bipolar electrogram (above the 1.5-mV normal cutoff of one classic ventricular study {C['marchlinski2000']}) with a crisp downstroke.")
    E("Fractionated signals cluster at pivot points and slow zones of re-entry circuits.",
      "Fractionated signals can occur at pivot points and slow zones of re-entry circuits.")
    E("— a tiny, blunt blip or nothing at all, well under 0.5 mV. Dead or replaced tissue generates almost no local signal. On a voltage map this paints purple. Scar alone is not the target — the channels and borders around it are.",
      f"— a tiny, blunt blip or nothing at all, below the 0.5-mV dense-scar cutoff {C['marchlinski2000']}. Dead or replaced tissue generates almost no local signal. On a voltage map this paints purple.")
    E("Mappers hunt for double potentials to prove an ablation line is truly blocked.",
      "Double potentials along a line are one sign that it blocks conduction (course module m22).")

    # ---------------------------------------------------------------- catheters
    E("<p>High-density mapping became possible when catheters grew from 4 electrodes to dozens of small, closely spaced ones. Smaller electrodes and tighter spacing mean sharper, more local signals.</p>",
      f"<p>High-density mapping became possible when catheters grew from a few electrodes to dozens of small, closely spaced ones. Smaller electrodes with closer spacing record more local signals {C['anter2015']}.</p>")
    E("five splines carrying 20 electrodes on the PentaRay, eight splines carrying 48 on the OCTARAY — giving a wide footprint of points per placement.",
      f"five splines carrying 20 electrodes on the PentaRay {UNV}, eight splines carrying 48 on the OCTARAY {C['masuda2024']} — giving a wide footprint of points per placement.")
    E("<p>A flat 4 × 4 paddle of 16 electrodes. Because it samples along two axes at once, the system can compute omnipolar signals — the true maximum voltage regardless of the direction the wave crosses the paddle.</p>",
      f"<p>A flat 4 × 4 paddle of 16 electrodes {UNV}. Because it samples along two axes at once, the system can compute omnipolar signals {C['magtibay2019']} — an amplitude that depends much less on the direction the wave crosses the paddle (course module m23).</p>")
    E("<p>An expandable basket with 64 tiny electrodes on 8 splines. Paired with automated point acceptance, it collects very high-density maps quickly — the platform's defining strength.</p>",
      f"<p>An expandable basket with 64 small electrodes {C['anter2015orion']} on 8 splines {UNV}. Paired with an automated mapping system {C['sultan2019']}, it collects high-density maps — the platform's design goal.</p>")
    E("the classic tool for confirming pulmonary vein isolation during AF ablation.</p>",
      f"used to check pulmonary vein isolation during AF ablation {C['anter2015orion']}.</p>")
    E("<p>The treatment catheter (e.g. ThermoCool SmartTouch, TactiFlex, IntellaNav StablePoint families) senses tip contact force in grams, so lesion tags on the map reflect pressure, power and time — not just position.</p>",
      f"<p>The treatment catheter (e.g. ThermoCool SmartTouch {C['teijeira2018']}; TactiFlex and IntellaNav StablePoint {UNV}) senses tip contact force in grams, so lesion tags on the map reflect pressure, power and time — not just position. Contact also changes the voltage recorded {C['teijeira2018']}.</p>")
    E("<p>A balloon carrying ultrasound transducers and electrodes that hovers in the chamber without touching the wall, reconstructing charge density over the whole chamber from a single beat.</p>",
      f"<p>A balloon carrying ultrasound transducers and electrodes that hovers in the chamber without touching the wall, reconstructing charge density over the whole chamber at once {C['pope2022']}.</p>")

    # ---------------------------------------------------------------- glossary
    E("Ablating across the isthmus breaks the loop; it is the highest-value target in flutter and many VTs.'",
      "Blocking conduction across the isthmus interrupts the loop.'")
    E("Encircling the pulmonary veins with ablation lesions so their triggers cannot reach the left atrium — the cornerstone ablation strategy for atrial fibrillation. Proven by demonstrating entrance and exit block.'",
      f"Encircling the pulmonary veins with ablation lesions so their triggers cannot reach the left atrium — the established ablation approach for atrial fibrillation {C['pope2022']}. Isolation is checked by testing for entrance and exit block {C['anter2015orion']}.'")
    E("Too little gives weak lesions; too much risks injury. A key input to lesion-quality tags.'",
      f"An input to lesion tags; contact also changes the voltage recorded {C['teijeira2018']}.'")
    E("to derive the electrogram’s maximum amplitude and direction, independent of the angle the wavefront crosses the catheter.'",
      f"to derive the electrogram’s amplitude and the wavefront direction largely independently of the angle the wave crosses the catheter {C['deno2017']}.'")
    E("3D mapping’s big practical win is letting teams work with minimal or near-zero fluoroscopy, cutting radiation for patient and staff.'",
      f"3D mapping locates catheters without X-ray {C['gepstein1997']}, which can reduce fluoroscopy use.'")
    E("A non-contact reconstruction (AcQMap) of the electrical charge pattern on the chamber wall, computed from a floating balloon’s electrodes via an inverse solution — a whole-chamber map from a single beat.'",
      f"A non-contact reconstruction (AcQMap) of the electrical charge pattern on the chamber wall, computed from a floating balloon’s electrodes via an inverse solution — a whole-chamber map {C['pope2022']}.'")

    # ---------------------------------------------------------------- quiz
    E("why:'A centrifugal bullseye is the fingerprint of a focal source — ablate the red centre.'",
      "why:'A centrifugal bullseye is the fingerprint of a focal source.'")
    E("opts:['The catheter is new','The wavefront travelled along the bipole’s axis','The map is very dense','The reference is in the coronary sinus']",
      "opts:['The catheter is new','The wave travelled at right angles to the bipole’s axis','The map is very dense','The reference is in the coronary sinus']")
    E("why:'Bipolar amplitude depends on wavefront direction — the blind spot omnipolar mapping was designed to remove.'",
      "why:'Bipolar amplitude depends on wavefront direction: a wave crossing at right angles to the bipole reads small (course module m23) — the blind spot omnipolar mapping was designed to reduce.'")
    E("{q:'Before ablating a VT isthmus you identified on a map, the classic cross-check is…',opts:['Ablate and see','Entrainment pacing from the site','Raise the voltage threshold','Delete half the points'],a:1,why:'Entrainment — matching fusion and a post-pacing interval within ~30 ms of the cycle length — confirms the site is in the circuit.'}",
      "{q:'Which pacing test checks whether a site you identified on a map is part of a re-entry circuit?',opts:['Changing the reference catheter','Entrainment pacing from the site','Raising the voltage threshold','Deleting half the points'],a:1,why:'Entrainment compares the paced rhythm and the post-pacing interval with the tachycardia to judge whether the site is in the circuit (course module m11).'}")

    # ---------------------------------------------------------------- checklist
    E("<li><b>Window set right?</b> — the window of interest must cover the full cycle length</li>",
      f"<li><b>Window set right?</b> — in re-entry, maps degrade when the window of interest is shorter than the cycle length {C['koawing2015']}</li>")
    E("<li><b>Voltage direction-checked?</b> — a wave crossing electrodes end-on reads falsely low</li>",
      "<li><b>Voltage direction-checked?</b> — a wave crossing at right angles to a bipole reads falsely low</li>")
    E("<li><b>Scar or artefact?</b> — confirm low voltage with contact and a second look</li>",
      f"<li><b>Scar or artefact?</b> — low voltage can also come from poor contact {C['teijeira2018']} or wave direction</li>")
    E("<li><b>EGMs inspected?</b> — never trust the colour without reading the underlying signals</li>",
      "<li><b>EGMs inspected?</b> — the colour is only as good as the signals behind it</li>")
    E("        <li><b>Endpoint proven?</b> — isolation or block must be demonstrated, not assumed</li>\n", "")

    # ---------------------------------------------------------------- footer: status, references, further reading
    refs = []
    for k in REFS:
        e = entries[k]
        authors = [clean(a).strip() for a in e["author"].split(" and ")]
        names = ", ".join(a.split(",")[0] for a in authors[:3] if a != "others")
        if len(authors) > 3 or "others" in authors:
            names += " et al."
        doi = e.get("doi", "")
        refs.append(f'<li id="ref-{k}">{html.escape(names)} ({years[k]}). {html.escape(clean(e["title"]))}. '
                    f'<i>{html.escape(clean(e["journal"]))}</i>. '
                    f'<a href="https://doi.org/{doi}">doi:{doi}</a></li>')
    E("<p style=\"margin-top:12px\">Sources — manufacturers' and independent descriptions of the platforms above:</p>\n    <div class=\"sources\">",
      "<p style=\"margin-top:12px\"><b style=\"color:var(--ink2)\">Status.</b> Draft, pending clinical review. Written by the course "
      "author with the Muse tool and edited to the course rules: description instead of advice, citations for facts, "
      "items without a source marked unverified. Text CC BY 4.0, code MIT; the hero drawing is original.</p>\n"
      "    <p style=\"margin-top:12px\"><b style=\"color:var(--ink2)\">References</b> (published studies used as sources):</p>\n"
      "    <ol class=\"refs\">" + "".join(refs) + "</ol>\n"
      "    <p style=\"margin-top:12px\">Further reading — manufacturers' and agency pages (not used as sources for the facts above):</p>\n"
      "    <div class=\"sources\">")

    # ---------------------------------------------------------------- apply
    out = s
    for old, new in edits:
        n = out.count(old)
        if n != 1:
            print(f"edit matched {n} times (expected 1):\n  {old[:160]}")
            return 1
        out = out.replace(old, new)

    # Page-view counting: the same snippet as every Quarto page (assets/analytics.html). It loads only on the live
    # site, and only once a Cloudflare token is set there; the page works the same without it.
    if out.count("</body>") != 1:
        print("expected exactly one </body>")
        return 1
    analytics = (ROOT / "assets" / "analytics.html").read_text(encoding="utf-8")
    out = out.replace("</body>", analytics + "</body>")
    Path(out_path).write_text(out, encoding="utf-8")
    print(f"wrote {out_path} ({len(out.encode())} bytes, {len(edits)} edits, {out.count(UNV)} unverified tags)")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else OUT))
