# Decisions log

Non-trivial choices, newest first. Each entry: date, decision, why, and how to undo it.

## 2026-11-27 · Search visibility fixes for openepengineering.org

- **Sitemap canonical alignment and git-accurate `lastmod`:** Quarto wrote `/index.html`,
  `/glossary/index.html`, and `/formula-sheet/index.html` into `_site/sitemap.xml` even though
  `canonical-url: true` sets `<link rel="canonical">` to the trailing-slash directory URLs (`/`),
  and stamped every page with the build timestamp on every deploy. `tools/update_sitemap.py` now
  rewrites each sitemap `<loc>` to match the page's `<link rel="canonical">`, sets `<lastmod>` from
  each source file's latest git commit (with `fetch-depth: 0` in `deploy-pages.yml`), and orders
  URLs deterministically with the homepage first.
- **Homepage social card and domain-brand association:** Quarto picked the 256×256 inline logo on
  `index.qmd` for `og:image`/`twitter:image` instead of the 1200×630 `og-card.png`. Setting
  `image: assets/logo/og-card.png` fixes link previews. `index.qmd`, `about.qmd`, and `README.md`
  now explicitly connect **Open EP Mapping Lab** with **openepengineering.org** / **Open EP
  Engineering** in `<title>`, `<meta name="description">`, visible prose, and JSON-LD (`WebSite`,
  `Organization`, `Course`, aligned with `Open EP Mapping Lab contributors` in `CITATION.cff`).
- **Site-wide Open Graph & structured data (`filters/seo-schema.lua`):** every Quarto page now
  emits `<meta name="robots" content="index, follow, max-image-preview:large">`, `og:url`, and
  `og:type`, and top-level pages (`about`, `course-map`, `formula-sheet`, `ai-competencies`,
  `useful-links`, `glossary`) emit schema.org + `BreadcrumbList` JSON-LD.
- **Undo:** revert this commit; off-repo indexing steps (Google Search Console verification and
  sitemap submission, Bing Webmaster Tools, GitHub topics) are managed outside git.

## 2026-11-27 · AI disclosure in the footer; readable citation BibTeX in dark mode

- **AI disclosure (author's request):** every page's footer now says "Developed using AI: Claude
  and Gemini" on its own line under "Education only. Not for clinical use." It links to "How the
  content is written and checked" on the About page, which now names both assistants (Claude by
  Anthropic, Gemini by Google). `tests/test_ai_disclosure.py` keeps the footer and About in step.
  The standalone Learning hub keeps its own status note.
- **Dark-mode fix:** Bootstrap prints plain `<pre>` text in black. Syntax-highlighted code blocks
  were fine, but the BibTeX in each page's Citation box is plain text, so it was nearly invisible
  on the dark theme.
  - Fix: `$pre-color` in the dark theme, and a code-block panel for that BibTeX in both themes.
  - Guard: `tests/test_theme.py` checks the contrast.

## 2026-11-27 · How to cite the course, and page-view counts

- **Decision (author):** let people cite the course, and count page views. The author chose a group
  author, "Open EP Mapping Lab contributors", and Cloudflare Web Analytics for counting.
- **Citation, in three places that tests keep in step (`tests/test_citation.py`):**
  - `CITATION.cff` (schema 1.2.0, validated with `cffconvert`, now in `requirements.txt`). GitHub
    shows it as "Cite this repository". `preferred-citation` gives the year, 2026.
  - Site-wide `author` (a literal name, so BibTeX keeps the group whole), `citation` and
    `google-scholar` in `_quarto.yml`. Every page gets a "Citation" box with BibTeX and a formatted
    reference, plus citation meta tags that Zotero and Google Scholar read. The formatted reference
    uses the site's existing Chicago style, which title-cases page titles.
  - "How to cite" on the About page, for the whole course, linked from the footer ("Cite this
    course").
- **Title block:** the site-wide author would appear under every page title, repeating the
  citation box, so `.quarto-title-meta` is hidden. No page sets a date (tested), so nothing else is
  hidden.
- **DOI:** not yet. Connecting the repository to Zenodo and publishing a GitHub release would mint
  one, and Zenodo reads `CITATION.cff`. That needs the author's own Zenodo sign-in.
- **Page views:** `assets/analytics.html`, on every Quarto page and added to the Learning hub by
  `tools/build_learning_hub.py`.
  - Off until the Cloudflare site token is set. The token is public: it is part of every page.
  - Loads only on openepengineering.org, so local previews and CI are never counted. Never loads
    when the browser sends Global Privacy Control or Do Not Track.
  - Cloudflare describes the beacon as using no cookies or local storage and no fingerprinting, so
    no consent banner is needed.
  - The page works the same without it. This is the one outside request on the Learning hub; its
    offline test allows exactly this snippet.
  - Privacy note on About ("Page views and privacy").
- **Tests:** `tests/test_analytics.py` serves the snippet as if from the live host, with every
  outside call intercepted. It checks four cases: with a token on the live site it loads Cloudflare's
  beacon; with no token it does nothing; local hosts are never counted; Global Privacy Control and
  Do Not Track are respected.
- **Undo:**
  - Remove `assets/analytics.html` from `include-after-body` and from the hub build. To pause
    counting only, set the token to "".
  - For citations, remove `author`, `citation` and `google-scholar` from `_quarto.yml`, and the
    CSS rule.

## 2026-11-26 · Videos and courses on the Useful links page

- **Decision (author):** add YouTube videos, lectures and university material on EP and mapping to
  "Useful links", starting from the author's bookmarks and adding the most-watched, most useful items.
- **What was added:** a new first section, "Videos and courses":
  - three **watch paths**: new to cardiac EP; how maps are made; the engineer's track;
  - a **library of 40 items** in ten topics, each with its source, length, YouTube views, level and a
    **Read next** link to the matching course module;
  - **channels worth following**, and a note on how the list was made.
- **Single source:** `links/videos.yml`. `tools/build_video_links.py` writes `links/_videos.md`,
  which the page includes. Watch-path totals are summed by the tool, never typed by hand.
- **How items were chosen (2026-11-26):**
  - YouTube was searched per topic with results sorted by view count, in the built-in browser.
  - Kept: societies, universities, hospitals, journals and established educators.
  - Titles, channels, lengths and view counts were copied as YouTube showed them, and the page
    prints the date. YouTube no longer shows dislikes, so popularity means views.
  - One-line descriptions say only what the title, the channel or the page itself shows.
- **Author's bookmarks:** 8 of 9 kept and marked "★ Author's pick".
  - The "Dr. Mitch Tan" playlist is the Texas Heart Institute's Cardiac Electrophysiology
    collection, linked there.
  - Left out: the Memorial Cardiac and Vascular Institute channel, which holds only one- to
    two-minute promotional clips.
  - The three neuroscience lectures sit under "Beyond the heart", where the inverse-problem,
    stimulation-mapping and open-data ideas carry over.
- **Also left out:**
  - Manufacturers' channels, to keep the list vendor-neutral. The test lists the names it rejects.
  - Duke's Coursera course "Bioelectricity: A Quantitative Approach": its Coursera page returns
    404.
- **Named people:** the 2026-11-22 rule removed a watchlist of physicians' X accounts. Lecturers
  are now credited only as the source of their own public lecture, as on any citation. The test
  docstring says so.
- **Layout:** tables on wider screens. On phones each row becomes a card (title, level,
  description, then source, length, views and module). Level labels carry the meaning in words;
  the colored dot is only a visual aid.
- **Guard:** `tests/test_useful_links.py`:
  - the data is complete and the generated file is current;
  - YouTube links and view formats are valid;
  - every "Read next" module exists;
  - no manufacturer channels;
  - watch-path totals are computed;
  - the retired course and the promotional channel stay out.
- **Undo:** remove the section and the include from `useful-links.qmd`, then delete `links/`
  and `tools/build_video_links.py`.

## 2026-11-25 · Feedback button that opens GitHub issues

- **What:** a **Feedback** button on every page (`assets/feedback.html`) opens a short form: kind of
  feedback, message, and optionally the text the reader selected. Sending it creates an issue labeled
  `feedback` in the course repository.
- **How "automatic" works:** a static site cannot hold a GitHub token, so the form posts to a small
  Cloudflare Worker (`services/feedback-worker/`). The Worker holds the token as a secret, checks the
  input and the Cloudflare Turnstile spam check, and calls GitHub's issue API. The token is
  fine-grained: this repository only, Issues read and write. Cloudflare was chosen because the
  domain's DNS is already there. This adds `services/` to the repository layout (CLAUDE.md §8) and
  one hosted component to the stack (CLAUDE.md §7). The site itself stays static.
- **Before the Worker is deployed** (the endpoint in `assets/feedback.html` is empty), the button
  opens a prefilled GitHub issue that the reader submits with their own account. Nothing else
  changes when it is switched on.
- **Privacy:** issues are public. The form says so, asks readers not to include personal or patient
  information (CLAUDE.md §6), and collects no name, email or IP address. The Turnstile script loads
  only when a reader opens the form, so pages make no outside calls until then.
- **Abuse:** every submission must pass Turnstile, and each token works once. The Worker accepts
  only the course site's origin and limits message length. Reader text goes into code blocks, so it
  cannot @mention people or add links, and the issue title holds only the kind and the page path.
- **Tests stay offline:** `tests/test_feedback.py` runs the Worker's Node tests (Turnstile and GitHub
  mocked) and drives the form in Chromium with every outside call intercepted. CI now installs
  Chromium before `pytest`.
- **Label added by a workflow (2026-11-25, same day):** the prefilled link first carried
  `labels=feedback`. The repository had no such label, and the GitHub iPhone app failed on submit
  (GitHub's website ignores an unknown label). Now neither route sets labels:
  `.github/workflows/label-feedback.yml` labels every issue titled "Feedback (…)" with the
  workflow's own token, and creates the label the first time. Readers need no permission for it.
- **Undo:** remove `assets/feedback.html` from `include-after-body` in `_quarto.yml`. To stop only
  the automatic sending, set `endpoint: ""`, then delete the Worker in Cloudflare and revoke the
  token on GitHub.

## 2026-11-23 · Shorter menu, search box in the menu, and a dark theme

- **Our own design, not a copy.** The author shared another course site's menu as a reference. We
  kept only the general pattern, which is common across documentation sites: a short menu with a
  "More" list, a search box and a dark-mode switch. The look comes from this course: the isochrone
  band, the activation-color underline and the recording-monitor dark theme. No text, styles or
  code were taken from that site (CLAUDE.md §6).
- **Menu:** the logo and title link home, then Course map, Learning hub, Useful links, About and
  "More" (Glossary, Formula sheet, AI competencies, Pilot module, Errata, Disclaimer). The
  separate Home item is gone. The LinkedIn icon stays on the right.
- **Wavefront underline.** On hover or keyboard focus the activation colors sweep under a menu
  item, like a wave crossing an isochronal map. The current page keeps the full band. The sweep is
  turned off for readers who ask for reduced motion.
- **Current page marked by a small script** (`assets/nav-current.html`). Quarto marks "Course
  map" as current on every page, because the course sidebar is site-wide. The script marks the
  real page with `aria-current="page"`. Module pages mark "Course map", and pages under "More"
  mark the "More" button. Without JavaScript nothing is marked, which is harmless.
- **Search box in the menu** (`search: location: navbar, type: textbox`), with a "/" key hint.
- **Dark theme ("night lab")** in `assets/theme-dark.scss`, layered after `theme.scss`. It is
  modeled on an EP recording screen in a dimmed lab. The home-page electrogram becomes a green
  monitor trace on a dark grid. The first visit follows the reader's system setting, and the
  switch overrides it. The colors in `theme.scss` became `!default` so the dark layer can
  override them; `tests/test_theme.py` checks this. Every text color meets WCAG AA (4.5:1) in
  both themes; the lowest is 5.4:1 (gray text on the light-gray panels).
- **Demos stay on a light panel in the dark theme.** The demo scripts draw with fixed colors
  meant for white paper. Restyling 149 demos for dark mode would risk breaking colors that carry
  meaning, such as activation scales. A lit panel keeps them exactly as designed.
- **The Learning Hub stays light.** It is a self-contained page built by
  `tools/build_learning_hub.py`, outside the Quarto theme.
- **Undo:** restore the previous `navbar` block and `theme: [cosmo, assets/theme.scss]`, then
  delete `assets/theme-dark.scss`, `assets/nav-current.html` and `tests/test_theme.py`.

## 2026-11-22 · Technical SEO, Learning Hub crawlability, and IP/trademark clarifications

- **Why:** an audit of copyright/IP hygiene and Google Search ranking found no copyright violations
  but identified brand-disambiguation/trademark gaps (conflation with `openep.io` and outdated AcQMap
  maker attribution) and technical SEO gaps (missing `robots.txt`, no canonical URLs, 6 core pages
  without meta descriptions, a 256×256 OG image, missing module/glossary JSON-LD, and an unindexed
  Learning Hub with JS-replaced tab panels).
- **IP & trademark hygiene:**
  - Added explicit non-affiliation notices with OpenEP (`openep.io`) on `index.qmd`, `about.qmd` and
    `disclaimer.qmd`.
  - Broadened the trademark list in `disclaimer.qmd` to cover all commercial system, catheter and
    software marks named across the course and Learning Hub.
  - Clarified `LICENSE-CONTENT` to note self-hosted IBM Plex fonts (SIL OFL 1.1) and exclude the
    project logo and site icons from CC BY 4.0 to protect brand identity.
  - Updated AcQMap's maker line on the Learning Hub to note the 2025 sale to EnChannel Medical.
- **Technical SEO & crawlability:**
  - Added `robots.txt` pointing to `https://openepengineering.org/sitemap.xml` and enabled
    `format.html.canonical-url: true` in `_quarto.yml`.
  - Added 60–160-character `description` summaries to `course-map.qmd` (via `tools/sync_curriculum.py`),
    `glossary/index.qmd`, `formula-sheet/index.qmd`, `ai-competencies.qmd`, `disclaimer.qmd` and
    `errata.qmd`.
  - Kept the topic-first `pagetitle` convention introduced on `main` (PR #116).
  - Created a 1200×630 social preview card (`assets/logo/og-card.png`) for `website.image` and
    Learning Hub Open Graph / Twitter metadata.
  - Added `filters/seo-schema.lua` to emit `max-image-preview:large`, per-module `LearningResource`
    + `BreadcrumbList` JSON-LD, and glossary `DefinedTermSet` JSON-LD; expanded home-page `Course`
    JSON-LD with `alternateName`, `educationalLevel`, `teaches`, `author` and `sameAs`.
  - Updated `tools/build_learning_hub.py` to add full meta/OG/Twitter/canonical/JSON-LD tags and to
    keep all tab panels (`workflow`, `systems`, `modes`) in the DOM using `hidden` so crawlers can
    index every platform comparison without clicking.
  - Added `tools/update_sitemap.py` (run after `quarto render` in `ci.yml` and `deploy-pages.yml`)
    so `learning-hub/index.html` is included in `_site/sitemap.xml`.
- **Guards:** expanded `tests/test_search_metadata.py` and updated `tests/test_learning_hub.py` to
  allow passive `<link rel="canonical">` tags while continuing to block fetched external resources.
- **Undo:** revert the PR commit; no module text, equations, demos or labs were altered.

## 2026-11-22 · Author's LinkedIn link

- **Decision (author):** show the author's public LinkedIn profile in the usual places:
  - an icon at the right of the navbar
  - an icon in the center of the page footer
  - a link in "Who makes it" on the About page
- **How:** the address is stored once in `_variables.yml` (`author.linkedin`), and the About page
  uses `{{< var author.linkedin >}}`. Quarto doesn't expand variables in `_quarto.yml`, so the navbar
  and footer repeat the address; `tests/test_author_links.py` checks that the copies agree. The icon
  is the LinkedIn glyph from the Bootstrap Icons font that Quarto bundles, so it works offline. Each
  icon-only link has an `aria-label` for screen readers.
- **Not added:** the author's name in the structured data, because no name was given.
- **Undo:** remove the navbar and footer items, the `author` block in `_variables.yml`, the sentence on
  the About page and the test.

## 2026-11-22 · Search-engine basics: module summaries, About page, link previews, Course markup

- **Why:** the author asked for help ranking in search. The site had no meta description on any of
  its 55 module pages, no About page and no structured data. Google's guidance puts helpful,
  trustworthy content first, and weighs trust signals more heavily for health-related topics.
- **Module summaries:** each module has a hand-written `description` of 90–160 characters, built from
  its title and topics, with no new numbers or claims. Quarto uses it as the page's meta description
  and shows it as a lead line under the title, styled in `.quarto-title-block .description`.
- **About page (`about.qmd`, navbar right):**
  - What the course is, who maintains it (the GitHub account only; no personal details were
    given), and how the content is written and checked.
  - It says that drafts are prepared with an AI assistant (Claude) and checked under the course
    rules, which matches this file and CLAUDE.md §5.
  - It states the current status: all 55 modules are drafts and none has been reviewed.
  - It covers scope, credits, license and contact. The author can add a short biography.
- **Link previews:** `website.open-graph` and `website.twitter-card` are on, with the logo as the
  preview image.
- **Structured data:** the home page carries schema.org JSON-LD for `WebSite` and `Course` (free,
  online, CC BY 4.0). Google's richer "course info" result also needs a study time for a
  self-paced course, which isn't added because no figure has been chosen yet.
- **Search titles:** each module has a `pagetitle`, its title without the "mNN · " code. The
  browser tab, search results and link previews now lead with the topic words, and Google shows
  only about 60 characters of a title. The page heading, breadcrumbs and sidebar keep the code.
  The module template carries both new fields.
- **Guard:** `tests/test_search_metadata.py`.
- **Undo:** remove the `description` and `pagetitle` lines, `about.qmd` and its navbar entry, the
  three `website` keys and the `include-in-header` block in `index.qmd`.

## 2026-11-22 · "Useful links" tab

- **Decision (author):** add the author's "Cardiac EP Intelligence Library" page as a navbar tab called
  "Useful links". It is rewritten as a normal course page, `useful-links.qmd`, in the site's style.
- **Copyright check:**
  - The text is the author's own. Searches for its most distinctive sentences found no matches
    elsewhere, it quotes nothing, and it contains no images.
  - Lists of links and the names of journals, societies and companies are not protected text.
    Company names are used only to identify the companies (CLAUDE.md §6).
  - As course content, the page is under CC BY 4.0.
- **Other problems found and fixed (author's choices):**
  - **Named physicians removed.** Seven physicians' X handles were listed as a "monitoring" watchlist,
    and the page itself said the handles were unconfirmed. Only the HRS, ESC Journals and ACC
    accounts remain, each confirmed.
  - **Reframed as a neutral learner resource.** The market-research parts are dropped: "competitive
    intelligence", the pain-point table, the tracker fields with "business relevance", the roadmap
    and the monitoring cadence. Companies are listed with links only, with no product claims
    (CLAUDE.md §5).
  - **Out-of-date company removed.** Acutus Medical has left the mapping business; its mapping
    platform was sold to EnChannel Medical in 2025.
  - **Links fixed.** Three journal addresses were not the journals' homepages (JCE, PACE, Journal of
    Arrhythmia); they now point to Wiley Online Library. Four other links had moved: EHRA (new ESC
    site), EP Lab Digest (HMP Global), FDA recalls (the old address returned 404) and J&J's
    electrophysiology page.
- **Link check, 2026-11-22:**
  - 22 links opened in a browser, including the societies, FDA databases, companies and X
    accounts.
  - Four publisher sites showed a bot check, so they were confirmed by web search instead.
  - PubMed searches are generated from their query strings.
  - Searching X needs a signed-in account, and the page says so.
- **Guard:** `tests/test_useful_links.py` (navbar, https only, organization accounts only, and the
  addresses found wrong stay out).
- **Undo:** delete `useful-links.qmd`, its navbar entry and the test.

## 2026-11-19 · Rename "Interview questions" to "Practice questions"

- **Decision (author):** the section is now called "Practice questions". Its contents and its
  rules are unchanged: at least 10 questions numbered Q1, Q2, …, each with a model answer. The short
  "Self-check" quiz keeps its name.
- **What changed:**
  - The heading in all 55 modules and the template.
  - The intro line under it, now "In your answer, say which assumptions you are making" instead of
    "In a real interview, …".
  - In-text cross-references ("interview Q10" is now "practice Q10").
  - The content tests, the home page, README, curriculum, course map and module outlines.
  - CLAUDE.md §1, §3, §8 (`practice/` folder), §10 and §11.
- **Kept:** the "Interview prep" learning path. Preparing for job interviews is still a real use of
  the course; its description now points to the practice questions. Older entries in this log are
  not rewritten.
- **Links:** the section's anchor changes from `#interview-questions` to `#practice-questions`. No
  page in the site linked to the old anchor; outside links to it would land at the top of the module.
- **Undo:** reverse the replacements; the commit touches only names, not question content.

## 2026-11-18 · Home page: logo beside the title

- **Decision (author):** show the logo on the home page as well as in the browser tab.
- **How:** `tools/make_favicons.py` also writes `assets/logo/logo-mark.png` (256 px, cropped to the
  drawing, for a 128-px display). The default title block can't hold an image, so `index.qmd` has no
  `title`; it draws its own header (logo, one `h1`, subtitle). `pagetitle` keeps the browser-tab
  title, and `description` gives the page a search-engine summary. Quarto 1.11 still printed a bare
  title with `title-block-style: none`, so that option was not used. Styles are in `assets/theme.scss`
  (`.home-header`), with a smaller layout below 576 px.
- **Undo:** restore `title` and `subtitle` in `index.qmd`, and remove the header block and its styles.

## 2026-11-18 · Fix: module counts on the home page and README

- **Problem:** the home page button said "See all 45 modules", and the README said "45 modules in
  seven parts". Both were written by hand before Part VIII took the course to 55 modules in eight
  parts. The status text was also out of date: it said only the pilot was being written and that
  the other 35 modules were planned. In fact all 55 have a draft, none has been reviewed, and every
  clinical section is pending. The course map was already right, because it is generated from
  `docs/curriculum.md`.
- **Fix:** corrected the counts and the status text. `test_hand_written_counts_match_the_curriculum`
  checks every "N modules" and "N parts" in `index.qmd` and `README.md` against the curriculum.
- **Undo:** revert the text and remove the test.

## 2026-11-17 · Site icon from the author's logo

- **Decision (author):** use the author's heart-and-gears logo as the browser-tab icon instead of the
  browser's default globe. The logo is stored at 512 px in `assets/logo/logo.png`.
- **How:** `tools/make_favicons.py` crops the logo to a square, places it on a white rounded tile
  (so it stays visible on dark tabs), and widens the strokes for small sizes so the lines survive. It
  writes `favicon.png` (64 px, linked from every page via `website.favicon`), `favicon.ico` (16, 32,
  48 px) and `apple-touch-icon.png` (180 px) at the site root. The Learning Hub had an empty icon
  (`data:,`); a build edit now links it to the same `favicon.png`. `tests/test_site_icons.py` checks
  the sizes and the links.
- **License:** the logo is supplied by the author, not drawn for the course, and it is not a
  vendor or third-party mark. Unless the author says otherwise, it falls under CC BY 4.0 like the
  rest of the content; many projects exclude their logo instead, which would need a line in
  `LICENSE-CONTENT`.
- **Undo:** remove `favicon` and the two icon resources from `_quarto.yml`, the hub build edit, the
  icon files, the script and its test.

## 2026-11-17 · Fix: resolve every TODO(source) on the module pages

- **Scope:** the ten open markers in m27, m28, m29, m30, m33, m34 and m36. One branch with one commit
  per module, because every module change also needs this log entry; separate PRs would conflict here.
- **How each source was checked:** PubMed metadata for every paper; full text (PMC) for any value
  taken from a table or the methods. The FDA records were read on the FDA 510(k) database itself.
- **m27:** blood 0.748 S/m and myocardium 0.281 S/m at 500 kHz, and A = 7.39 × 10^39 s⁻¹,
  Ea = 2.577 × 10^5 J/mol, from one cardiac RF model (Pérez 2022). The page keeps the authors'
  caveats: the database is uncertain below 1 MHz, and the Arrhenius values are not cardiac-specific.
- **m28:** membrane values from a cardiomyocyte electroporation model (Scuderi 2023). Lethal
  thresholds from ex vivo perfused hearts (Kos 2023), called preliminary as the authors do. "Beating
  heart" was changed to "ex vivo perfused hearts", which is what the study used.
- **m29:** the chain and its 40–250 Hz / 20 Hz values come from Li 2016, which credits Botteron.
  Botteron and Smith 1995 is still not cited directly; its abstract does not describe the chain.
- **m30:** localization values reuse Gepstein 1997 and Wittkampf 1999. Respiratory motion comes from
  Shechter 2004 (4.9 ± 1.9 mm caudal shift in 10 patients).
- **m33:** the defaults stay illustrative, with cited scale (Steinhaus 1989, De Pooter 2018,
  Williams 2018). **No measured clinical spread of annotation error was found;** a reviewer may
  prefer to keep a marker until one is.
- **m34:** the m34-d3 defaults changed from 20 to 35 mm/s (coronary-artery speeds, Shechter 2006)
  and from 100 to 25 ms (40 Hz, a general-purpose electromagnetic tracker, Yaniv 2009). The update
  rates of commercial mapping systems were not found in public sources, and the page says so.
- **m36:** K231207, K231415 and K241227 confirm regulation 870.1425 with product code DQK.
- **Computed values are tested:** Arrhenius times and the conductivity ratio (m27), the membrane time
  constant per micrometer (m28), and the m34-d3 default bound and slider values (m34).
- **Undo:** revert the per-module commits.

## 2026-11-17 · Fix: deploy only the newest commit on main

- **Problem:** PRs #106, #107 and #108 merged within minutes. Each merge ran CI, and each CI run that
  passed started a deploy of the commit it checked. The CI run for #106 finished last, so the deploy
  that went live was built from #106, without the Learning Hub added in #108. Re-running that deploy
  rebuilt the same old commit.
- **Fix:** the deploy job runs only when the commit CI checked is still the newest on `main`
  (`github.event.workflow_run.head_sha == github.sha`; for `workflow_run` events `github.sha` is the
  newest commit on the default branch). Deploys for older commits are skipped. A manual run
  (`workflow_dispatch`) is unchanged and always builds the newest commit.
  `tests/test_deploy_workflow.py` keeps the guard in place.
- **Undo:** remove the `head_sha == github.sha` clause from the `if:` in `deploy-pages.yml` and delete
  the test.

## 2026-11-17 · Learning Hub tab

- **Decision (author):** add the author's "Electrophysiology Mapping System — Learning Hub & Explorer" page,
  made with Muse, as a separate navbar tab, "Learning hub". It is a self-contained HTML page (simulator,
  workflow, systems explorer, map types, electrogram lab, glossary, quiz, roadmap), not a module, so the
  curriculum and module numbering do not change.
- **How it is built:** the original page is kept in `learning-hub/source/`, without its embedded raster
  image. `tools/build_learning_hub.py` applies 67 named, exact-match edits and writes
  `learning-hub/index.html`. Only the built page is published (`_quarto.yml` resources).
  `tests/test_learning_hub.py` checks that the build is current, that the page runs offline, that every
  citation resolves to a references.bib entry with a DOI, and that no ablation advice remains.
- **Edits to meet CLAUDE.md** (the author left the content question open; the recommended option was
  taken):
  - Fonts: self-hosted IBM Plex instead of Google Fonts. Plex Serif 400–600 and Mono 500–600 were added to
    `vendor/fonts/ibm-plex/` from @fontsource 5.3.0, under the same OFL.
  - Image: the AI-generated hero image is replaced by an original SVG drawing (author's choice), generated
    by `learning-hub/source/make_hero_svg.py`.
  - Advice reworded as description: "ablate the red centre", "highest-value target", "never ablate on
    colour alone", and the procedural endpoints.
  - Numbers: simulator cycle lengths are labeled illustrative. The voltage cutoffs cite Marchlinski 2000.
    The "~30 ms" post-pacing interval is replaced by a description that cites Stevenson 1993 and links to
    m11.
  - Physics: the page said bipolar voltage is small when the wave travels *along* the bipole. It is small
    when the wave travels at right angles to it (m23), so four places are corrected.
  - Product facts: cited to peer-reviewed papers where found (17 references, 5 new). The rest are tagged
    "unverified" on the page and listed in `errata.json` (E2). Market claims ("most widely installed",
    "five platforms dominate") are removed.
- **Undo:** remove the navbar entry and the resource line in `_quarto.yml`, and delete `learning-hub/`,
  the build script and its test.

## 2026-11-17 · Fix: duplicate citation keys in references.bib

- **Problem:** three keys appeared twice. `kligfield2007` and `magtibay2019` were two copies of the same
  paper. `beinart2011` named **two different papers**: left atrial wall thickness on CT (cited by m40,
  m48 and m51) and respiratory compensation in mapping (cited by m19 and m20). Pandoc keeps the last
  entry for a duplicated key, so m40, m48 and m51 showed the respiratory-compensation paper as the
  source of their wall-thickness values. The duplicate came in with m19 (2026-11-14).
- **Change:** the respiratory-compensation paper is now `beinart2011resp`, cited from m19 and m20 and
  the m20 outline. The shorter copies of `kligfield2007` and `magtibay2019` are removed. A new test,
  `test_reference_keys_are_unique`, fails on any repeated key.
- **Undo:** not advised. Reverting brings back the wrong reference on m40, m48 and m51.

## 2026-11-17 · Custom domain changed to openepengineering.org

- **Decision (author):** serve the site at `https://openepengineering.org/`, the domain the author
  registered, instead of `https://open-ep-mapping-lab.org/` (2026-11-05 entry below). The course
  keeps its name, Open EP Mapping Lab; only the address changes.
- **Change:** `site.url` in `_variables.yml`, `site-url` in `_quarto.yml`, the site link in
  `README.md` and the comment in `.github/workflows/deploy-pages.yml`. The repo and Colab URLs do not
  change. The address test in `tests/test_content_rules.py` checks that these agree.
- **Needs the author:** in Settings → Pages → Custom domain, replace the old domain with
  `openepengineering.org`. At the registrar, add four A records for the apex (185.199.108.153,
  185.199.109.153, 185.199.110.153, 185.199.111.153), optional AAAA records (2606:50c0:8000::153
  to 2606:50c0:8003::153), and a `www` CNAME to `raghavendrasri.github.io`. Then verify the domain
  and tick "Enforce HTTPS". Deployment is by GitHub Actions, so no `CNAME` file is needed.
- **Undo:** restore `https://open-ep-mapping-lab.org/` in the same four files and in Settings →
  Pages.

## 2026-11-15 · m26 stages 1–6, map quality and uncertainty

- **m26** (Map quality and uncertainty): five tested equations (GP posterior, closed-form leave-one-out, per-point
  error budget, nearest-point distance, greedy maximum-variance sampling), one simulation and one exact demo, clinical
  correlate (pending review), 12 interview and 6 self-check questions, a Python lab (A–E). This completes Part IV.
- **Euclidean kernels only.** GP interpolation on the atrial manifold is cited, not implemented; a geodesic kernel is
  left as an exercise.
- **Error budget per point.** The budget feeds the GP's observation noise, so map uncertainty combines measurement
  error and interpolation without double counting.

## 2026-11-15 · m25 stages 1–6, conduction velocity estimation

- **m25** (Conduction velocity estimation): five tested equations (velocity from the gradient and its noise bias,
  two-point error, triangle covariance, plane-fit covariance, potential-based velocity and the cross-clique bias), two
  exact demos, clinical correlate (pending review), 12 interview and 6 self-check questions, a Python lab (A–E).
- **A cross-shaped clique stands for omnipolar methods.** It isolates the finite-difference bias in closed form.
  Published omnipolar methods add field-loop and fitting steps that are described, not reproduced.
- **The velocity map uses the m30 eikonal solver** with speeds of 1.0 and 0.6 m/s from Heil and colleagues.

## 2026-11-15 · m24 stages 1–6, interpolation, activation maps and isochrones

- **m24** (Interpolation, activation maps and isochrones): five tested equations (linear interpolation error, IDW,
  harmonic interpolation, isochrones, block and coverage), one exact and one simulation demo, clinical correlate
  (pending review), 12 interview and 6 self-check questions, a Python lab (A–E).
- **Harmonic interpolation as the mesh method.** It reuses the m06 cotangent Laplacian, needs no tuning, and shows the
  free-boundary artifact clearly. Radial basis functions (m18) and Gaussian processes (m26) are left to those modules.
- **Coverage shares a label with block.** Both are short consequences of sampling, so `eq-m24-block` carries both
  results.

## 2026-11-15 · m23 stages 1–6, voltage mapping

- **m23** (Voltage mapping): four tested equations (amplitude against height and spacing, direction, noise floor,
  log-normal cutoffs), one exact and one approximate-model demo, clinical correlate (pending review), 12 interview and
  6 self-check questions, a Python lab (A–E).
- **Exact amplitudes at 2-mm spacing.** The small-spacing formula overstates a 2-mm bipole's amplitude by about half at
  1 mm height, so demos and the lab compute peak-to-peak on the closed-form signals instead.
- **Log-normal tissue populations are illustrative.** No source gave distributions in a form we could use; the cutoffs
  themselves are cited.

## 2026-11-15 · m22 stages 1–6, electrogram annotation

- **m22** (Electrogram annotation): six tested equations (LAT and reference error, steepest downstroke and bipolar
  peak, onset bias, threshold jitter, window of interest, far-field sharpness and template), one exact and one
  approximate-model demo, clinical correlate (pending review), 12 interview and 6 self-check questions, a Python lab
  (A–E).
- **One electrogram model throughout.** Annotation rules are compared on the m03 arctangent front, so their offsets are
  exact for that model; real signals add curvature, fractionation and filtering.
- **Smooth noise in the jitter checks.** Noise is low-pass filtered so the threshold-crossing formula applies; the lab
  also shows how fast noise breaks the derivative-based rule.
- **m06 spectrum made deterministic.** CI on #97 failed once in `test_m06_meshes.py::test_spectrum`: asking for exactly
  16 eigenvalues ends at the edge of the sphere's 7-fold l = 3 cluster, and Lanczos sometimes missed one member.
  `meshes.spectrum` now computes 8 extra eigenvalues from a fixed start vector and returns the smallest k.

## 2026-11-14 · m21 stages 1–6, image integration

- **m21** (Image integration): five tested equations (Otsu's threshold, Dice and Jaccard, landmark least squares,
  ICP, point-to-plane linearization), one simulation and one exact demo, clinical correlate (pending review), 12
  interview and 6 self-check questions, a Python lab (A–E).
- **Global threshold as the baseline.** Segmentation is shown with Otsu's threshold, smoothing and the largest connected
  component; learned segmentation stays in m40.
- **Exact correspondences in the ICP experiments.** Mapped points are samples of the image surface, so failures come
  only from local minima, not from noise or deformation. This isolates the starting-pose effect.
- **2D ICP in the demo.** The demo runs brute-force nearest neighbors in the browser; 3D is in the lab.

## 2026-11-14 · m20 stages 1–6, geometry from catheter positions

- **m20** (Geometry from catheter positions): five tested equations (convex hull, inflate–fill–shrink closing,
  Laplacian and Taubin smoothing, mesh volume and Hausdorff distance, mean surface distance), two simulation demos,
  clinical correlate (pending review), 12 interview and 6 self-check questions, a Python lab (A–E).
- **2D reconstruction in the lab and demo.** A 3D closing needs many thousands of positions and large arrays, too slow
  and memory-hungry for CI, so the reconstruction is shown on a 2D slice. Volumes and smoothing are checked in 3D.
- **No marching cubes in code.** It would need scikit-image, which is not a course dependency; surfaces are compared on
  voxel boundaries, and marching cubes is cited.

## 2026-11-14 · m19 stages 1–6, motion and drift

- **m19** (Motion and drift): six tested equations (breathing model, gating duty cycle, reference subtraction,
  surrogate regression, drift estimation, averaging), two exact demos, clinical correlate (pending review), 12
  interview and 6 self-check questions, a Python lab (A–E).
- **A cos^(2n) breathing model.** It is periodic and asymmetric, as Lujan et al. describe breathing, and gives a
  closed-form gating duty cycle. The page does not attribute this exact form to the paper, whose full text was not
  read.
- **Cardiac gating by analogy.** It is treated as the same duty-cycle trade with the cardiac cycle in place of the
  breath, rather than with a separate model.

## 2026-11-14 · m18 stages 1–6, hybrid and dielectric localization

- **m18** (Hybrid and dielectric localization concepts): five tested equations (affine correction, radial-basis
  correction, coverage, inverse-variance fusion, complex conductivity), a simulation demo of a hybrid correction and an
  approximate-model dielectric demo, clinical correlate (pending review), 12 interview and 6 self-check questions, a
  Python lab (A–E).
- **A generic hybrid correction.** No peer-reviewed description of a commercial algorithm was found. The module uses a
  Gaussian radial-basis correction with an affine part, and says products do not publish theirs.
- **Illustrative tissues.** Single-relaxation parameters for "blood-like" and "wall-like" tissue are chosen to show the
  idea, not taken from measurements; the page points to Gabriel et al. (1996) for real spectra.
- **Glossary.** The existing "Radial basis function" entry gained an m18 link instead of a new plural entry.

## 2026-11-14 · m17 stages 1–6, impedance localization

- **m17** (Impedance localization): six tested equations (patch-pair potential, axis nonlinearity, linear map, field
  scaling as a local metric, interface stretch, precision), two exact demos, clinical correlate (pending review),
  12 interview and 6 self-check questions, a Python lab (A–E).
- **Field scaling as a metric tensor.** Known electrode spacings give l^2 = dphi^T M dphi, linear in the six entries
  of M = (J J^T)^-1. This is our own formalization of the principle; the page says products do not publish theirs in
  this form.
- **Unbounded homogeneous torso.** It gives closed forms for the nonlinearity; inhomogeneity is shown with a 1D layered
  model rather than a full torso solve.

## 2026-11-14 · m16 stages 1–6, magnetic localization

- **m16** (Magnetic localization): seven tested equations (dipole field, coil voltage, measurement model and least
  squares, covariance, range sensitivity, five degrees of freedom, distortion), an exact precision demo and an
  approximate-model distortion demo (first-order bias), clinical correlate (pending review), 12 interview and 6
  self-check questions, a Python lab (A–E).
- **A generic generator.** Three coil trios on a 150-mm circle and a single-coil sensor stand in for any product; the
  layout and noise are labeled illustrative. The point is the scaling, not the numbers.
- **The r^4 law is stated as a far-field result.** Near the coils the predicted error grows more slowly; the page and
  demo say so.

## 2026-11-14 · m15 stages 1–6, patient safety

- **m15** (Patient safety): five tested equations (capacitive leakage and its sum, current density at an electrode,
  defibrillation protection network, RF filter order, demodulation), two exact demos, clinical correlate (pending
  review), 12 interview and 6 self-check questions, a Python lab (A–E).
- **Physics, not standard limits.** IEC 60601-1 could not be read. The only numeric limit used is the 50 µA
  single-fault value as reported in peer-reviewed papers (Swerdlow 1999, Jonsson 2005). The normal-condition CF limit
  appears only in vendor and training web pages, so it is not quoted. Clinical thresholds come from Swerdlow et al.
  (1999).
- **Illustrative values are labeled.** Capacitances, mains voltages, defibrillation voltages, RF amplitudes and the
  nonlinearity coefficient are free choices for teaching, listed as illustrative on the page.

## 2026-11-14 · m14 stages 1–6, biopotential front ends

- **m14** (Biopotential front ends): eight tested equations (modes and CMRR, difference amplifier, instrumentation
  amplifier, electrode mismatch, driven right leg, noise, Wilson central terminal, converter and oversampling), two
  exact demos, clinical correlate (pending review), 12 interview and 6 self-check questions, a Python lab (A–E).
- **No product values.** Amplifier noise densities, resistor tolerances, input capacitances and the common-mode
  voltage are adjustable illustrative choices; the page says so. No standard's limits are quoted because the standards
  could not be read.
- **Title-only citations.** The two classic Webster papers have no abstracts on PubMed; they are cited as pointers,
  and the derivations stand on our own SymPy checks.

## 2026-11-14 · m13 stages 1–6, catheter design

- **m13** (Catheter design): six tested equations (spreading resistance, bipole direction, spatial aliasing against
  height, basket spacing, least-squares contact force and its noise), two exact demos, clinical correlate (pending
  review), 12 interview and 6 self-check questions, a Python lab (A–E).
- **Spacing rule from the Poisson kernel.** The sharpest gradient signal a planar front can make at height h has
  spectrum exp(-|k|h), which gives a closed-form aliased-energy fraction exp(-2 pi h / spacing). It makes the point
  that spacing must scale with height without a simulation.
- **Contact force as least squares.** Sensing is described generically (a spring element and a few strain sensors);
  the three-sensor model matches the published optical design without using any vendor's calibration.
- **Fill distance measured over the electrode band.** No basket electrode reaches the poles, so whole-sphere fill
  distance is dominated by the polar gap and hides spline spacing.

## 2026-11-14 · m12 stages 1–6, the surface ECG

- **m12** (The surface ECG and the forward problem): seven tested equations (centric dipole in a sphere, off-center
  series, lead vector, Einthoven's law, augmented leads and WCT, frontal axis, forward problem), two exact demos
  (limb leads and axis; lead vectors of an off-center heart), clinical correlate (pending review), 12 interview and 6
  self-check questions, a Python lab (A–E).
- **Spherical torso, not a realistic one.** It gives closed forms and an exact series; inhomogeneous torsos stay in
  m32.
- **No real-data part.** PhysioNet was not reachable from the build environment, so a PTB-XL part could not be tested
  before CI; m37 already uses PTB-XL.

## 2026-11-14 · m11 stages 1–6, the EP study

- **m11** (The EP study): four tested equations (intervals, AV nodal recovery curve, Wenckebach point, post-pacing
  interval), two exact demos (Wenckebach ladder; PPI against distance), clinical correlate (pending review), 12
  interview and 6 self-check questions, a Python lab (A–E).
- **No human normal intervals are quoted.** No accessible primary source for them was verified; the AV node uses
  rabbit values from Reid et al. 2003 with an illustrative recovery time constant, labelled as such.
- **Entrainment is simulated on the m10 ring with a dead-end branch**, which reproduces PPI − TCL ≈ 2d/CV and the
  rate-related lengthening Stevenson et al. describe.

## 2026-11-14 · m10 stages 1–6, arrhythmia mechanisms

- **m10** (Arrhythmia mechanisms): five tested equations (wavelength, circuit, restitution map, closed-form alternans
  onset, focal activation) plus a tested phase-singularity count, two exact demos (restitution cobweb; ring with
  wavelength and gap), clinical correlate (pending review), 12 interview and 6 self-check questions, a Python lab
  (A–E).
- **Topological charge is linked to m29**, not given a new label.
- **Ring reentry is started from a fully developed pulse.** Starting from an excited segment with a refractory block
  launched a backward wave when the block recovered before the segment repolarized; cutting a window from a
  traveling pulse avoids that.
- **Spirals use Barkley's model with illustrative parameters.** A Mitchell–Schaeffer spiral with the m08 parameters
  needs a domain of tens of centimeters; the topology is the same.
- **The rotor debate is reported from both sides** (CONFIRM and a later two-center series), with no verdict.

## 2026-11-14 · m09 stages 1–6, propagation

- **m09** (Propagation): six tested equations (cable, bidomain, monodomain, velocity scaling, anisotropy, curvature),
  a simulation demo (cable velocity against conductivity and grid) and an exact demo (elliptical isochrones and
  apparent velocity), clinical correlate (pending review), 12 interview and 6 self-check questions, a Python lab (A–E).
- **Mitchell–Schaeffer kinetics with the m08 parameters** in every simulation, so velocities and $D$ values connect
  across Part II. m33 keeps its own illustrative constants.
- **Clerc's resistance ratios are used as relative conductivities** (intracellular longitudinal = 1); no absolute
  conductivities are quoted.

## 2026-11-14 · m08 stages 1–6, action potentials

- **m08** (Action potentials and ionic models): seven tested equations, two simulation demos (FitzHugh–Nagumo phase
  plane; Mitchell–Schaeffer restitution), clinical correlate (pending review), 12 interview and 6 self-check
  questions, a Python lab (A–E). Part II, so no Octave copy.
- **No detailed atrial model is implemented.** Their parameter tables were not accessible to verify; the page
  describes them from their abstracts and uses Mitchell–Schaeffer for all numbers.
- **Mitchell–Schaeffer parameters come from a secondary source** (Nieto Ramos et al. 2023), which reports
  $\tau_{\text{open}}$ = 150 ms and $\tau_{\text{close}}$ = 120 ms as based on the original paper. Flagged in the PR
  for a check against the original.
- **The closed-form APD is presented as the time the excited state disappears.** The measured APD at
  $v_{\text{gate}}$ is 25–40 ms longer; the tests check both statements.

## 2026-11-12 · m07 stages 1–6, inverse problems

- **m07** (Inverse problems and regularization): seven tested equations (model and condition number, continuation
  across a source-free layer, naive SVD inverse, filters, error budget, parameter choice, Bayesian reading), an exact
  error-budget demo and a simulation deblurring demo, clinical correlate (pending review), 12 interview and 6
  self-check questions, a Python lab (A–E) and an Octave copy (A–E).
- **Worked example is harmonic continuation, not a torso model.** It is exact, one-dimensional and diagonal in the
  Fourier basis, and it reproduces the m03 front shape (width $w$ continued by $h$ gives $w + h$), so the module needs
  no boundary-element code. m32 keeps the torso problem.
- **Discrepancy principle left unattributed.** Its original source was not looked up; the rule is described and its
  behavior shown with our own code.

## 2026-11-12 · m06 stages 1–6, meshes and geodesics

- **m06** (Triangle meshes, Laplace–Beltrami operators and geodesics): five tested equations (Euler's formula, per-face
  gradient and conduction velocity, cotangent Laplacian, sphere spectrum, heat method), two exact demos (lattice edge
  paths; cotangent edge weights), clinical correlate (pending review), 12 interview and 6 self-check questions, a
  Python lab (A–E) and an Octave copy (A–E).
- **Convergence is tested on typical, not worst, error.** With barycentric vertex areas the cotangent Laplacian's
  worst pointwise error on the icosphere stays near 0.25 at the 12 five-neighbor vertices; the tests check the median
  and integrated errors and assert that the worst error does not fall, and the page says so.
- **Heat method written from the paper**, with $t = h^2$ and the source vertex pinned in the Poisson step; no geometry
  package is used, so Python, Octave and the tests share one small implementation.

## 2026-11-12 · m05 stages 1–6, time–frequency tools

- **m05** (Time–frequency tools): seven tested equations (resolution, leakage, Welch variance, pulse-train spectrum,
  analytic signal, uncertainty, Morlet), two exact demos (resolution and leakage; Hilbert phase against activations),
  clinical correlate (pending review), 12 interview and 6 self-check questions, a Python lab (A–F) and an Octave copy
  (A–E).
- **Definitions stay in m29.** DF, OI and sinusoidal recomposition are linked, not repeated; m05 supplies the reasons
  they work and fail.
- **m29's TODO(source) on the preprocessing chain is not resolved here.** Botteron and Smith 1995 was checked on
  PubMed and its abstract does not describe the chain.

## 2026-11-12 · m04 stages 1–6, recording chain

- **m04** (Sampling, filtering and the EP recording chain): six tested equations (aliasing, quantization, RC
  high-pass, Butterworth, group delay, notch), an exact aliasing demo and an approximate-model filter demo on the m03
  unipolar electrogram, clinical correlate (pending review), 12 interview and 6 self-check questions, a Python lab
  (A–E) and an Octave copy (A–E) with core functions only.
- **Filters built by hand.** First- and second-order Butterworth sections via the bilinear transform, identical in
  Python, JS and Octave and checked against scipy, so no signal-processing package is needed in the labs or demos.
- **Published bands only from one study** (Delacretaz et al. 2001). No vendor defaults are described.

## 2026-11-12 · m02 stages 1–6, volume conduction

- **m02** (Volume conduction and Poisson's equation): five tested equations (Poisson, interface conditions, images,
  flux-conserving finite differences, reciprocity), an exact demo (images) and a simulation demo (SOR solver checked
  against images), clinical correlate (pending review), 12 interview and 6 self-check questions, a Python lab (A–D)
  and an Octave copy (A–D).
- **Conductivity ratios are parameters.** No blood or tissue value is asserted; none was verifiable from PubMed
  abstracts.
- **Octave copy is Octave-specific.** Named functions inside a script must come before use in Octave and at the end in
  MATLAB, so the solver is written with anonymous functions, which needs Octave's `merge` and chained indexing.

## 2026-11-12 · m01 stages 1–6, bioelectric sources

- **Part I started** (author request, 2026-11-12: "lets start with m01–m07"). One pull request per module, stacked;
  m03 is left as the existing pilot.
- **m01** (Bioelectric sources): six tested equations (point source, dipole, double layer, core conductor, dipole moment
  of a front, front as a line of dipoles), two exact demos, clinical correlate (pending review), 12 interview and 6 self-check questions,
  a Python lab (parts A–F) and an Octave copy (parts A–E), as CLAUDE.md §7 asks for Part I.
- **Relative units, as in m03.** No absolute conductivity or capacitance values: the PubMed records found for them
  had no abstracts with numbers. The only quantitative values are Clerc's anisotropy ratios (abstract).
- **The front's dipole moment and the m03 closed form.** m01 shows that a front of width w at height h equals a line
  of dipoles at height w + h, so m03's result follows from m01 without repeating its derivation.

## 2026-11-12 · AI competency map

- **New page `ai-competencies.qmd`** (author request, 2026-11-12): maps nine AI competency areas (machine learning,
  Bayesian networks, graphical models, logic, search, Markov decision processes, reinforcement learning, planning and
  game playing, AI and society) to EP uses and to existing modules, and says which areas are not yet taught. Linked
  from the navbar ("AI competencies").
- **Author's choice: a map, not new modules.** No module was added, dropped or renumbered. Each of m35 and m37–m47
  gets one "AI competency areas" bullet in its Further reading section, so the template headings are unchanged.
- **New sources, looked up on PubMed or arXiv:** brugada1991 (rule-based stepwise criteria), clavier2002 (hidden
  Markov model for P-wave delineation), muizniece2021 (Q-learning on simulated left atria; simulation only),
  madry2018 (adversarial training as a min-max problem). No Bayesian-network study in EP was cited: PubMed searches
  returned mostly Bayesian network meta-analyses, which are a different method.
- **No equations on the page,** so it adds no untested formulas. Undo: delete the page, its navbar and render
  entries, and the twelve bullets.
## 2026-11-12 · m48 stages 1–6, imaging across the EP workflow

- **m48** (Imaging across the EP workflow): five tested equations (PSF and two-point resolution, CNR, smoothing,
  wall visibility, likelihood ratios), two exact demos (thin walls at published resolutions; predictive values
  against prevalence), a question-to-modality table, clinical correlate (pending review), 12 interview and 6
  self-check questions, glossary and formula-sheet entries.
- **Thin-wall equation linked, not repeated.** The overview planned eq-m48-thin-wall; it is the same result as
  eq-m51-wall, so m48 links to it and adds the noise side (eq-m48-visibility) instead.
- **"Which modality for which question" is a table, not a demo.** Every interactive demo must have a slider and a
  readout that changes (render check); a filterable table had no natural slider. The table sits at the top of the
  derivations, and the second demo shows predictive values against prevalence. Undo: add a filter demo with a
  slider and restore the overview's plan.
- **CT resolution from one photon-counting system** (Rajendran et al. 2022, section-sensitivity FWHM 0.34 and
  0.64 mm). No source for conventional CT resolution was read; m51 keeps its illustrative 1-mm blur.
- **Pooled PPV against the formula.** The page and lab say the 41% reported and 54% from the formula need not agree,
  give PPV's concavity in prevalence as one reason, and do not attribute it to the meta-analysis.

## 2026-11-12 · m55 stages 1–6, capstone

- **m55** (Capstone): three tested equations (C-arm projection, FRE and TRE, error budget), an approximate-model demo
  (predicted TRE over a plane) and an exact demo (overlay on a projection), clinical correlate (pending review), 12
  interview and 6 self-check questions, glossary and formula-sheet entries.
- **Registration is used, not derived** (author decision 2): `epml.capstone` has a least-squares rigid fit and ICP for
  the lab, and the page points to m21 for the derivation.
- **TRE formula** from Fitzpatrick et al. 1998, checked against the restatement in Danilchenko and Fitzpatrick 2011;
  the lab shows where the first-order formula starts to underestimate (about 12% at 3 mm FLE on a clustered layout).
- **No scikit-image.** Surfaces are boundary voxels (`epml.imaging.surface`) rather than marching cubes, so no new
  dependency is needed.

## 2026-11-11 · m54 stages 1–6, nuclear imaging

- **m54** (Nuclear imaging in EP): four tested equations (decay, SUV, recovery coefficients of a wall, noise and a
  response rule), two exact demos (partial volume; decay and timing), clinical correlate (pending review), 12
  interview and 6 self-check questions, glossary and formula-sheet entries.
- **Recovery of the mean, not only the peak.** The plan named one recovery coefficient; the module derives both the
  maximum (the m51 wall formula) and the mean over the wall, because the cited sarcoidosis study used corrected means.
- **Response-rule statistics** added as eq-m54-change: the published 25% rule and the published ~10% test-retest
  figure give misclassification rates in closed form, checked by simulation.
- **birnie2014 cited by title only** (no abstract on PubMed), as the plan said.

## 2026-11-11 · m53 stages 1–6, lesion imaging and real-time MRI

- **m53** (Imaging ablation lesions and real-time MRI-guided EP): two tested equations (a gap in a blurred lesion
  line; real-time frame time), two exact demos (gap visibility; frame rate), clinical correlate (pending review),
  12 interview and 6 self-check questions, glossary and formula-sheet entries.
- **Gap visibility reuses m51's blur model.** The gap is the complement of a thin wall, so the page links to
  eq-m51-wall and derives only the 2-D separable form.
- **Kappa stays in m35.** The lab uses `epml.ml.cohen_kappa`; the page links to eq-m35-kappa instead of re-deriving it.
- **Electrograms in the scanner** use the filter chain reported in a review with illustrative waveforms, labeled as
  such; no recorded data were available under an open license.

## 2026-11-11 · m52 stages 1–6, cardiac MRI

- **m52** (Cardiac MRI for EP): six tested equations (Larmor, inversion recovery, relaxivity, ECV, inversion time
  for LGE, image intensity ratio and burden), an exact demo (signal against inversion time) and a simulation demo
  (burden against threshold on a synthetic wall), clinical correlate (pending review), 12 interview and 6
  self-check questions, glossary and formula-sheet entries.
- **Blood-scar contrast from one model.** Blood's post-contrast T1 is computed from the published myocardial values
  with @eq-m52-ecv and an illustrative native blood T1 and hematocrit, labeled as such, rather than quoted.
- **The synthetic wall is precomputed** (`tools/make_m52_d2.py` → `demos/m52-d2-wall.json`, ~100 kB) so the demo and
  the lab use the same data; a test checks the file is current.
- **Real data without an LGE set.** No openly licensed atrial LGE data set was found in this session, so lab part F
  uses the Decathlon heart MRI (already used in m40) to show blood-pool normalization only, and says it is not LGE.
- **Devices:** registry results only, without operating details or advice.

## 2026-11-11 · m51 stages 1–6, cardiac CT

- **m51** (Cardiac CT for EP): ten tested equations (Hounsfield units, iodine, Radon transform, central-slice
  theorem, filtered back-projection, Ram-Lak kernel, quantum noise, gating window, smeared disk, blurred thin wall),
  a simulation demo (sinogram and reconstruction) and an approximate-model demo (motion during the gating window),
  clinical correlate on pre-procedural CT (pending review), 12 interview and 6 self-check questions, glossary and
  formula-sheet entries.
- **Monoenergetic attenuation at 60 keV** (NIST), the same energy as m49, so the two modules share one table. Real
  CT is polyenergetic; the page says so. Undo: replace the constants in `epml.ct` with spectrum-weighted values.
- **Gating as T_rot/(2 N_src)**, checked against three published windows (within 6%), instead of a scanner-specific
  model. Coronary speeds stand in for cardiac motion because a published left atrial wall speed was not found.
- **Thin walls are owned by m51** (eq-m51-wall). m48's planned thin-wall equation will link here instead of
  re-deriving it.
- **Registration stays in m21** (author decision): m51 only contrasts the error a system reports with the error at a
  target, using the published studies.
- **No dose conversion factors.** The plan listed them "to verify"; noise against photon count is derived instead and
  dose quantities stay in m49.
- **Spelling in `docs/curriculum.md`:** "oesophagus" and "oedema" became "esophagus" and "edema" (American English,
  CLAUDE.md §9); the m51 and m53 titles changed only in spelling. Also "neighbours" in one glossary entry.

## 2026-11-11 · m50 stages 1–6, intracardiac echocardiography

- **m50** (ICE with TEE and TTE): five tested equations (echo time to depth with the speed-of-sound assumption,
  axial resolution, attenuation and reach, phased-array steering, frame rate), two exact demos (array factor;
  loss, reach and frame rate), clinical correlate on transseptal access and ICE-versus-TEE evidence (pending
  review), 12 interview and 6 self-check questions, glossary and formula-sheet entries.
- **Lightweight ultrasound** (author decision): no Doppler, harmonics or transducer design; the physics is written
  from scratch and limited to what explains an ICE image.
- **`epml.ice`**: ranging, n-cycle Hann bursts and echo overlap, attenuation budget, array factor and grating
  lobes, a small delay-and-sum simulator (single unfocused transmit, a stated simplification), a synthetic septum
  with tenting, and shells from tracked planes. Default values come from published sources (1540 m/s, ICE
  frequencies, myocardial attenuation); the rest is labelled illustrative.
- **No open ICE images** were found, so the lab is synthetic, in line with "open sources only".

## 2026-11-11 · Part VIII added (m48–m55), and m49 stages 1–6

- **Curriculum: 47 → 55 modules, eight parts.** The author approved Part VIII, imaging in electrophysiology, with
  eight modules after m47, so nothing was renumbered. Updated: `docs/curriculum.md` (new part and an "Imaging in EP"
  learning path), `tools/sync_curriculum.py` (slugs, short names, and "not yet scheduled" as the release for Part
  VIII, because the author has not chosen one), CLAUDE.md (scope, counts and ID range), and the generated pages.
  Plan and decisions: `docs/outlines/part8-overview.md`.
- **Author decisions:** registration stays in the existing modules (Part VIII links, it does not re-derive);
  ultrasound in m50 stays lightweight; open sources only; modules stay `draft` until an imaging collaborator reviews
  them; m49 and m50 first.
- **m49** (Fluoroscopy and radiation protection): five tested equations (attenuation, contrast, quantum noise,
  kerma-area product, staff dose), two demos (projection image with noise; staff dose), clinical correlate on
  radiation and low-fluoroscopy evidence (pending review), 12 interview and 6 self-check questions, glossary and
  formula-sheet entries.
- **`epml.fluoro`**: NIST attenuation coefficients at 60 keV, an ellipsoid chest phantom with exact line integrals
  (checked against ray marching), Poisson projection images, dose quantities, staff dose and reference-level
  methods. A single photon energy is a stated simplification.

## 2026-11-11 · m47 stages 1–6, data and deployment engineering

- **m47** (Data and deployment engineering): five tested equations (header conversion, majority of labellers,
  re-identification risk, affine quantization, quantization noise), two demos (quantizing a beat, an
  approximate model; re-identification risk in a synthetic registry, a simulation), clinical correlate on where
  data-pipeline issues arise in EP (pending review), 12 interview and 6 self-check questions, glossary and
  formula-sheet entries. Kappa and the label ceiling are reused from m35 rather than restated.
- **`epml.deploy`**: WFDB write, read and header edits; a plausibility audit with ranges learned from training
  data (no physiological thresholds); checksum manifests and a dataset version id; labeller simulation and
  majority votes; equivalence classes and re-identification risk on a synthetic registry; affine quantization,
  SQNR, per-tensor and per-unit weight quantization; a model card that refuses empty sections.
  **`epml.data`** gained `ptbxl_columns`, `ptbxl_headers` and `challenge2017_headers` (header files only).
- **HIPAA as the one legal example**, cited to HHS pages and marked as not legal advice; other jurisdictions are
  out of scope for now.
- **Stanford and NVIDIA:** Chambon et al. 2023 (de-identification of report text), Liang et al. 2024 (32,111
  model cards); Wu et al. 2020 (NVIDIA, integer quantization).

## 2026-11-11 · Two new Part VII modules (m46, m47), and m46 stages 1–6

- **Curriculum: 45 → 47 modules.** After a gap review of Part VII the author approved two modules:
  m46 (Trustworthy AI in EP) and m47 (Data and deployment engineering). They are added after m45, so no
  module was renumbered. Updated: `docs/curriculum.md`, `tools/sync_curriculum.py` (slugs and short names),
  CLAUDE.md (module counts and ID range), and the generated sidebar, course map and placeholder pages.
  Undo: remove the two rows and slugs, restore the counts, and rerun `tools/sync_curriculum.py`.
- **m46**: five tested equations (integrated gradients, split conformal sets, the FPR identity, the
  Mahalanobis score, the gradient-sign attack on a linear score), two demos (live conformal sets; exact
  PPV-versus-prevalence trade-off), clinical correlate on subgroup performance, explanations and tampering
  (pending review), 12 interview and 6 self-check questions, glossary and formula-sheet entries.
- **`epml.trust`**: integrated gradients (midpoint rule, with a closed form for logistic regression), a small
  NumPy network with input gradients, conformal sets (one threshold or one per class), group rates, a
  Mahalanobis score with a chi-square threshold, and gradient-sign attacks. **`epml.data.ptbxl_metadata`**
  reads age and sex from the checksum-verified PTB-XL table; sex is reported as the database's code.
- **Stanford:** kaur2023 (heart-failure AI-ECG disparities, Stanford Hospital) and ghorbani2020 (EchoNet
  interpretation). No NVIDIA source fitted this module.
- **`demos/m43-d2-corpus.json` regenerated** for the new glossary terms.

## 2026-11-11 · m45 stages 1–6 (Part VII capstone), and the first erratum

- **m45** (Evidence and regulation of AI in EP): three tested equations (sample size for sensitivity
  and specificity, net benefit, CUSUM), two demos (live drift simulation; exact sample-size curves),
  clinical correlate on where AI in EP stands on the evidence ladder (pending review), 12 interview and
  6 self-check questions, glossary and formula-sheet entries.
- **`epml.evidence`**: sample size, net benefit, CUSUM and run lengths, a TRIPOD+AI-style report card
  (numbers only), and a check of a model update against acceptance criteria written in advance. The
  check illustrates the idea of a PCCP; it is not a regulatory template.
- **First erratum (E1).** m37's lab unpacked `calibration_slope_intercept` in the wrong order and printed
  the intercept as the slope; fixed in the notebook and its generator, recorded in `errata.json` and on
  the errata page (now a table). No page text quoted the value.
- **Stanford and NVIDIA:** He et al. 2023 (blinded randomized trial with Stanford and Cedars-Sinai
  authors) and Wu et al. 2021 (Stanford analysis of FDA AI-device evaluations, cited by title because
  PubMed has no abstract); federated validation with NVIDIA FLARE and the EXAM study.

## 2026-11-11 · m44 stages 1–6, an agent whose guardrails sit outside the model

- **m44** (Agentic AI in EP): four tested equations (chain, check, escape, mixture), two demos
  (precomputed agent trace under eight guardrail settings; exact error-compounding curves), clinical
  correlate on remote-monitoring triage (pending review), 12 interview and 6 self-check questions,
  glossary and formula-sheet entries.
- **`epml.agent`**: tools with typed, unit-checked schemas, permission tiers, a policy (allowlist,
  sandbox, approval for writes), a step-limited loop, a JSON-lines audit log, a check that every
  number in an answer came from a tool, and a scripted stand-in model with chosen faults. **Writes that
  no person approved are never executed**, whatever the policy settings: they are only simulated, so
  the "guardrails off" runs in the demo and lab cannot touch files.
- **Published agent examples** (author's request): MedAgentBench and its follow-up (Stanford),
  AgentClinic (Stanford and Johns Hopkins), DeepRare, the PPG agent of Feli et al., agentic model
  search (preprint), ReAct, generative agents and DSPy (Stanford), NVIDIA's NeMo Guardrails.
- **`demos/m43-d2-corpus.json` regenerated** for the new glossary terms.

## 2026-11-11 · m43 stages 1–6, contrastive pretraining and an offline LLM-evaluation harness

- **m43** (Foundation models and large language models): eight tested equations (InfoNCE and its
  gradient, attention, score variance, TF-IDF, cosine, Wilson interval, questions needed), two demos
  (precomputed contrastive embedding; exact retrieval over the course glossary), clinical correlate
  (pending review), 13 interview and 6 self-check questions, glossary and formula-sheet entries.
- **`epml.foundation`** trains a small encoder with InfoNCE in NumPy (manual backward pass, Adam), so
  the core lab needs no PyTorch; part H repeats it with a 1-D CNN in PyTorch.
- **`epml.retrieval`** holds the TF-IDF index, ranking metrics, Wilson interval and an evaluation
  harness whose "model" is a scripted stand-in with planted faults (Part VII rule: no external AI
  services in CI). An optional notebook cell, skipped in CI, lets readers plug in their own model.
- **New generated demo files:** `demos/m43-d1-data.json` (from `tools/make_m43_d1.py`) and
  `demos/m43-d2-corpus.json` (from `tools/make_m43_d2.py`, rerun after glossary changes); both are
  checked by `tests/test_m43_demos.py`.
- **Stanford and NVIDIA:** Almanac (Zakka et al. 2024) and MedHELM (Bedi et al. 2025) from Stanford;
  NV-Embed (Lee et al., NVIDIA) as the example of a dense text-embedding model.
- **Last checksum pins.** The first CI runs that downloaded them (main, `5bfa3f2`) printed the
  SHA-256 of the Challenge 2017 `training/SHA256SUMS` list and of the MSD `Task02_Heart.tar` archive
  (whose MD5 matched MONAI's published value); both are now pinned in `data/registry.json`, so a
  changed file stops the lab. Also restored the m41 and m42 entries above, lost in a merge on main.

## 2026-11-11 · m42 stages 1–6, physics-informed fits without a deep-learning library

- **m42** (Physics-informed machine learning): six tested equations (eikonal residual, loss, RBF map,
  Levenberg–Marquardt step, ensemble statistics, slowness scaling), two simulation demos (precomputed
  data versus physics; live one-dimensional ensemble), clinical correlate on what method studies show
  (pending review), 12 interview and 6 self-check questions, glossary and formula-sheet entries.
- **`epml.pinn`** fits RBF activation maps with analytic gradients by Levenberg–Marquardt, so the core
  lab needs no PyTorch; part F repeats the homogeneous case with a PyTorch PINN.
- **New precomputed demo data:** `demos/m42-d1-data.json` (73 kB) from `tools/make_m42_d1.py`, checked
  against a fresh computation in `tests/test_m42_demos.py`.
- **NVIDIA and Stanford:** Raissi et al. 2020 (an NVIDIA-affiliated author, checked on PubMed) and
  NVIDIA PhysicsNeMo (software record); Sahli Costabal et al. 2020 with a Stanford co-author
  (affiliation checked on the publisher's PDF).
- **Undo:** revert the m42 commit.

## 2026-11-11 · m41 stages 1–6, synthetic lab only

- **m41** (Locating arrhythmia origins from the ECG): six tested equations (QRS integral in a
  double-layer model, least squares, geodesic error, pace-map correlation, GP posterior, expected
  improvement), a simulation demo of active pace-mapping and an exact one-dimensional GP and EI demo,
  clinical correlate on what localization studies show and what their references mean (pending
  review), 12 interview and 6 self-check questions, glossary and formula-sheet entries.
- **Forward model** (`epml.origins`): a uniform double layer on a closed ellipsoidal surface in an
  infinite medium, activation times from mesh edge paths. Labelled an approximate model; it gives the
  QRS integral the structure derived in the module.
- **No real data in this lab.** The candidate open database (Zheng et al. 2020, figshare) could not
  be reached from the build workspace to verify its licence and files. Recorded as an open point in
  the outline and the pull request rather than guessed.
- **Demo change from the overview:** m41-d2 is the one-dimensional GP and EI demo.
- **Undo:** revert the m41 commit.

## 2026-11-11 · Pin the PhysioNet checksum lists used by m37 and m38

- **Decision:** record the SHA-256 of `afdb-1.0.0/SHA256SUMS.txt` and `ptb-xl-1.0.3/SHA256SUMS.txt`
  in `data/registry.json`, as printed by the main-branch CI run of 2026-11-11 (commit 300e5ab).
  `epml.data.PhysioNetDB` now refuses a list that has changed. The CI checksum step prints every
  `SHA256SUMS*` file, so the Challenge 2017 list (`training/SHA256SUMS`) can be pinned next.
- **Undo:** remove the two entries.

## 2026-11-11 · m40 stages 1–6, nibabel, and MONAI in the PyTorch job

- **m40** (AI for cardiac imaging and substrate): eight tested equations (Dice–Jaccard, Hausdorff,
  ASSD, NSD, first-order offset, spheres, shifted wall, concordance index), two exact demos (metrics
  with a stray island; Dice against structure size), clinical correlate on DECAAF and DECAAF II and
  on an AI-built ICE shell (pending review), 12 interview and 6 self-check questions, glossary and
  formula-sheet entries.
- **Real data:** Medical Segmentation Decathlon Task02_Heart (20 labelled MRI volumes of the left
  atrium, CC BY-SA 4.0), downloaded in CI from the MONAI consortium's AWS Open Data bucket and checked
  against the MD5 value published in MONAI 1.6.1. Share-alike: nothing derived from these images is
  committed; the lab only prints numbers.
- **New dependency:** `nibabel` (MIT licence) in `requirements.txt`, to read NIfTI files.
- **CI:** the `labs-pytorch` job also installs MONAI (Apache-2.0) and sets `EPML_REQUIRE_MONAI=1`, so
  m40 part F runs MONAI's U-Net and Dice loss (the NVIDIA example the author asked for). Without
  MONAI the lab falls back to a minimal PyTorch U-Net.
- **Demo change from the overview:** m40-d2 compares structure sizes exactly instead of simulating a
  mask-to-shell pipeline; the shell question is lab part D.
- **Undo:** revert the m40 commit; remove `nibabel` and the MONAI install line.

## 2026-11-11 · m39 stages 1–6, and Part VII pull requests target main

- **m39** (AI on electrograms and maps): six tested equations (graph convolution, smoothing fixed
  point, Dice, lens area, focal loss, Gaussian mixture), two exact demos (graph smoothing; Dice
  against centroid distance), clinical correlate on the TAILORED-AF and RESTART trials as their
  papers report them (pending review), 12 interview and 6 self-check questions, glossary and
  formula-sheet entries.
- **Graph network in NumPy:** `epml.graphs.GCN` has hand-written gradients checked against finite
  differences, so the core lab needs no deep-learning library; part F repeats it in PyTorch.
- **Synthetic maps** reuse the eikonal model of m30 with 1.0 and 0.6 m/s (Heil et al. 2023);
  region sizes, timing noise and the voltage-like feature are illustrative.
- **Real data:** Intracardiac Atrial Fibrillation Database (ODC-By 1.0), distal bipole CS12, the
  first fourteen 4-s windows of each record (the free-wall records are longer and include drug
  delivery). Not yet run against the real files: CI is the first run.
- **Pull requests now target main.** The m38 pull request (#56) targeted the m37 branch and was
  merged there after m37 had reached main, so its commits never reached main. From now on every
  Part VII pull request targets main, and each module branch also carries the commits of earlier
  modules that are not yet merged; the diff shrinks as they land. This replaces the stacked-branch
  note in the m38 entry.
- **Undo:** revert the m39 commit.

## 2026-11-11 · m38 stages 1–6, and stacked Part VII branches

*Superseded in part: see the m39 entry for how pull requests are now targeted.*

- **m38** (Wearables and implantable monitors): seven tested equations, two exact demos
  (consecutive-window rule; review inbox), clinical correlate on ILR false alerts (pending review),
  12 interview and 6 self-check questions, glossary and formula-sheet entries.
- **Real data:** MIT-BIH Atrial Fibrillation Database, beat (.qrs) and rhythm (.atr) annotations
  only (`epml.data.load_afdb_rr`), ODC-By 1.0.
- **Stacked branches:** each Part VII module branch starts from the previous module's branch, and its
  pull request targets that branch, because the modules share files (data helpers, references,
  glossary, formula sheet). Merge in order m37, m38, …; after a merge GitHub retargets the next
  pull request to main when the merged branch is deleted (otherwise change its base by hand).
- **Undo:** revert the m38 commit.

## 2026-11-11 · m37 stages 1–6, and how Part VII modules are built

- **Process (author decision, 2026-11-11):** each Part VII module (m37–m45) goes through all six
  stages in one branch and one pull request, reviewed per module instead of per stage. Human
  sign-offs (`review_record.json`, clinical review) stay open. CLAUDE.md §10's per-stage stop is
  waived for Part VII only.
- **Libraries (author decision):** labs use NumPy and scikit-learn; each lab with a neural network
  also has an optional PyTorch part. CI runs those parts in a separate job, `labs-pytorch`, with the
  CPU-only PyTorch build and `EPML_REQUIRE_TORCH=1`; it sets `EPML_SKIP_REAL_DATA=1` because the main
  job already checks the downloads.
- **Data (author decision):** synthetic data always; real public data downloaded in CI and skipped
  offline. m37 uses PTB-XL 1.0.3 (CC BY 4.0) and the PhysioNet/CinC Challenge 2017 training set
  (ODC-By 1.0). `epml.data.PhysioNetDB` fetches files in parallel and checks each against the
  database's published SHA256SUMS.txt; the hash of that list is printed in CI and will be pinned in
  `data/registry.json` in a follow-up commit (the workspace cannot reach PhysioNet).
- **CI:** the lab step now gives each notebook its own 5-minute limit (`timeout 300`) instead of 5
  minutes for all labs together, which nine new labs would exceed. The job limit rose from 20 to 45
  minutes. The data cache key now follows `data/registry.json` and `epml/data.py`.
- **m37 content:** derivations with nine tested equations, two exact demos (receptive field;
  screening yield with prior shift), clinical correlate on AI-ECG-guided AF screening (pending
  review), 12 interview and 6 self-check questions, glossary and formula-sheet entries. The
  synthetic ECG (Gaussian waves after McSharry et al. 2003) uses illustrative values, flagged as
  such in every place it appears.
- **Stanford and NVIDIA work** (author request): cited where it fits the derivations, with
  affiliations checked on PubMed (Hannun 2019, Kaur 2023; Dayan 2021 with NVIDIA authors; NVIDIA
  FLARE on arXiv).
- **Undo:** revert the m37 commit; restore the old lab step in `.github/workflows/ci.yml`.

## 2026-11-10 · Part VII: AI in electrophysiology (m37–m45)

- **Decision (author request):** add a seventh part, "AI in electrophysiology", with nine planned
  modules, m37–m45. Titles and learning path are in `docs/curriculum.md`; scope, use cases
  (including agentic AI), planned equations, demos, labs, data sets and verified sources are in
  `docs/outlines/part7-overview.md`. Module count and numbering still need the author's approval
  in the pull request.
- **Why nine:** each covers a distinct data type or method with its own evidence base (surface
  ECG, wearables and implants, intracardiac signals, imaging, origin localization, physics-informed
  ML, foundation models and LLMs, agents, evidence and regulation). The overview lists merges the
  author may prefer.
- **Release:** Part VII is tagged v1.5 (after v1.0). `tools/sync_curriculum.py` gained `V15_PARTS`,
  slugs and sidebar names for m37–m45, and now writes the course-map count from the curriculum
  instead of a fixed "Thirty-six modules in six parts".
- **Rules:** `CLAUDE.md` §2 now lists AI methods in scope and adds three Part VII rules: report
  results as the study reports them, no external AI calls from labs or demos (scripted stand-in
  model in CI), and agents act only on course files with a human approving every write.
- **Sources:** about 60 papers were looked up on PubMed for the overview; bib entries are added
  when a module first cites them (stage 2). Six method papers (graph networks, PINNs, attention,
  sample size, CUSUM, decision curves) are marked `[unverified]` until stage 1.
- **Undo:** revert this commit and rerun `python tools/sync_curriculum.py`.
## 2026-11-06 · m33 stage 4: code lab

- **Author decisions (2026-11-06):** the lab stops at exporting files for openCARP, so CI never needs
  openCARP; the lab starts from a synthetic case rather than an OpenEP example case.
- **The case:** a 20-mm sphere (illustrative size) with a slow region (0.6 m/s) in normal tissue
  (1.0 m/s, both Heil et al. 2023) and a non-conducting scar; 200 points with 1-mm position error,
  1-ms annotation noise and a 25-ms offset (illustrative). Voltage is in relative units, to avoid
  quoting mV thresholds without an atrial source.
- **Changed from the first draft of the lab:** a planned "three regions with block" twin had no effect
  because the very-low-voltage label was nearly empty; it was replaced by the same two-region twin at
  two thresholds, which shows the real lesson (fitted speeds absorb labeling errors).
- **`epml/twin.py`:** `calibrate_regions` can hold regions at a fixed speed (for block) and cap
  evaluations; new `write_opencarp`, `read_opencarp` and `tangent_fibres`, with a round-trip test.
  Formats from the CARP/openCARP file-format page and openCARP's mesh writer (`Tr n0 n1 n2 tag`).
- **Runtime:** about 25 s here, well inside the 5-minute CI limit.
- **Undo:** revert the m33 stage 4 commit.

## 2026-11-05 · m33 stage 3: demos

- **m33-d1 (calibrate a twin)** runs entirely in the browser: an eikonal model on a 30 × 30 mm,
  1-mm grid, fitted with Levenberg–Marquardt (one speed per square region, closed-form offset) and
  scored by 5-fold cross-validation. The JS eikonal visits triangles in fast-sweeping order for
  speed (about 0.3 ms per solve); it uses the same local update as the Python solver, and
  `tests/test_m33_demos.py` checks that both reach the same times. Default 9 regions, so the slow
  region shows on first load.
- **Cited defaults:** 1.0 m/s and 0.6 m/s from Heil et al. (2023). Point count, annotation noise and
  the slow region's size are illustrative inputs; typical clinical values stay `TODO(source)`.
- **m33-d2 (eikonal vs reaction–diffusion)** is precomputed by `tools/make_m33_d2.py` (about a
  minute, 481 KB of JSON) from the course's own Mitchell–Schaeffer sheet, with conductivities tuned
  to the cited velocities by eq-m33-cv-scaling. Four scenarios (planar, point pacing, slow region,
  isthmus) replace the outline's free sliders, because the reaction–diffusion runs are too slow for
  the browser. The data file carries the generator's hash; a test checks it and the numbers quoted
  in the text.
- **Shared plot helpers** gained `drawField` (viridis or a blue–white–vermillion diverging map, with
  optional isochrone-like bands), `addSelect` and `addButton`. On screens narrower than 520 px the two
  maps stack.
- **Undo:** revert the m33 stage 3 commit.

## 2026-11-05 · Custom domain: open-ep-mapping-lab.org

- **Decision (author):** serve the site at `https://open-ep-mapping-lab.org/` instead of a
  `github.io` address.
- **Why:** the planned move to `open-ep-mapping-lab.github.io` had not happened, so that address
  did not exist, and since PR #20 the site's code-lab and Colab links pointed at a repository that
  did not exist yet. A custom domain removes the personal name from the site address without moving
  the repository, and keeps working if the repository moves later (GitHub redirects repository
  links after a transfer, but not `github.io` Pages addresses).
- **Change:** `_variables.yml` site URL is the custom domain; the repo URL is the repository's real
  location today (`raghavendrasri/open-ep-mapping-lab`). `_quarto.yml`, `README.md` and the lab
  notebooks follow, as the address test requires.
- **Needs the author:** register the domain, add it under Settings → Pages → Custom domain, add the
  DNS records GitHub lists (four A records for the apex, optional AAAA, and a `www` CNAME to
  `raghavendrasri.github.io`), verify the domain, then tick "Enforce HTTPS". With deployment by
  GitHub Actions, no `CNAME` file is needed.
- **Moving to the organization** stays optional. If it happens, change `repo.url` (and the Colab
  URL) here and the custom domain keeps the site address unchanged.
- **Undo:** restore the previous URLs in `_variables.yml`, `_quarto.yml`, `README.md` and the
  notebooks, and remove the custom domain in Settings → Pages.

## 2026-11-04 · m33 stage 2: derivations and equation tests

- **Isotropic surface twin** fitted with the m30 eikonal solver; the anisotropic eikonal is derived
  and checked on a flat sheet, but fibres are not used in the fit (outline question 3, recommended
  option).
- **Velocity-to-conductivity scaling derived** from the invariance of the monodomain equation and
  checked on a Mitchell–Schaeffer cable; Costa et al. (2013) is cited for iterating on real meshes.
- **Cross-validation shown on a polynomial example** in the tests (fast and unambiguous); the lab
  will apply it to the twin.
- **No openCARP in tests.** Nothing in stage 2 needs it; whether CI may install it for the lab stays
  open (outline question 2).
- **`epml/ionic.py` now refuses unstable explicit steps** (D dt / dx² > 1/2), after a test with a
  larger diffusion coefficient blew up silently.
- **Undo:** revert the m33 stage 2 commit.

## 2026-11-04 · m32 stage 2: derivations and equation tests

- **Tikhonov, filter factors and λ rules defined in m32** (`eq-m32-*`), since m07 is not written
  yet; m07 can take them over later.
- **Axisymmetric nested-sphere model** (Legendre polynomials) for the closed-form forward matrix and
  all tests. It shows the ill-posedness exactly and needs no external geometry.
- **Hansen's L-curve papers** are not in PubMed; both were checked by DOI (SIAM Review 1992,
  10.1137/1034115; SIAM J Sci Comput 1993, 10.1137/0914086).
- **EDGAR terms** are taken from its user guide (checked 2026-11-04), cited as an official document.
  No EDGAR data is committed. How the lab gets data stays open (outline question 1).
- **Undo:** revert the m32 stage 2 commit.

## 2026-11-04 · m31 stage 2: derivations and equation tests

- **All equation tests use synthetic signals**, so they run without downloading iafdb; the code lab
  (stage 4) uses the real records.
- **Block bootstrap instead of sample bootstrap**, tied to the design effect from m35. The block
  length is the analyst's choice and must exceed the correlation time; the test shows the coverage
  gap on AR(1) data rather than claiming a rule for block length.
- **Facts about iafdb** come from its PhysioNet page, checked on 2026-11-04, including that
  amplitudes are uncalibrated; the page's inconsistent ECG-lead count is stated, not resolved.
- **Open:** the real-data badge question (outline question 1) affects stage 3 demos, not this stage.
- **Undo:** revert the m31 stage 2 commit.

## 2026-11-04 · m30 stage 2: derivations and equation tests

- **m30 written before m20 and m22–m26**, with its own minimal versions (projection, inverse-distance
  interpolation, plane-fit velocity, RMSE and fill distance), labelled `eq-m30-*`. When those
  modules are written, m30 will cite their equations instead.
- **Eikonal ground truth only** (no reaction–diffusion option yet). The solver in
  `epml/mapping.py` uses iterative triangle updates rather than ordered fast marching: simpler to
  read, same fixed point. Tests compare it with exact answers on a plane (≤ 5 % worst case, improving
  with refinement), a sphere (mean error < 2 %) and a detour around a line of block.
- **Own geometry:** flat grids and icospheres generated in code. No external mesh or new dependency
  (pyvista is not needed for stage 2).
- **Undo:** revert the m30 stage 2 commit.

## 2026-11-04 · m29 stage 2: derivations and equation tests

- **DF, OI and Hilbert phase defined in m29** (`eq-m29-*`), since m05 is not written yet. When m05
  is written it can define the general tools and m29 can cite them; the formula sheet will keep one
  copy.
- **Mitchell–Schaeffer model in `epml/ionic.py`**, shared with m33. Tests use illustrative
  parameters only; the module states no parameter values until they are sourced.
- **Preprocessing chain not attributed.** The abstract of Botteron and Smith (1995) does not
  describe the band-pass / rectify / low-pass chain, so the module states the chain and marks its
  origin and filter values `TODO(source)`; Botteron and Smith is not cited yet.
- **Recomposition wavelet period** set to the cycle length in this course; only the slope-weighted
  amplitudes are attributed to Kuklik et al.
- **Undo:** revert the m29 stage 2 commit.

## 2026-11-04 · m28 stage 2: derivations and equation tests

- **Spheroidal cells described, not derived.** The PMC copy of Kotnik and Miklavčič (2000) has no
  full text, so its spheroid formula could not be checked; the module states the generalization in
  words and keeps the sphere (Schwan) result. Revisit if the full text is read.
- **Charging time constant derived here** from the $l = 1$ solutions with a capacitive membrane
  (SymPy test), instead of quoting it.
- **New equation eq-m28-zones** (reversible and irreversible shells), the simplest model of the
  "core and halo" seen on post-PFA maps.
- **Bench thresholds quoted only as bench values** (Avazzadeh 2021, 2022), with tissue thresholds
  `TODO(source)`.
- **Undo:** revert the m28 stage 2 commit.

## 2026-11-04 · m27 stage 2: derivations and equation tests

- **Outline questions answered with the recommended options** (the outline was merged without
  answers): generic weighted index only, no commercial formula; 1D spherical model in the text and
  lab, 2D axisymmetric only in the demo; cryoablation out of scope.
- **Hemisphere instead of a disk electrode** in eq-m27-spreading. The hemisphere result follows from
  the sphere by symmetry and needs no outside source; the disk result (Newman) is still unverified.
- **New equation eq-m27-power-fraction** (share of heating within radius $r$ is $1 - r_0/r$). It is
  the clearest way to show that heating is concentrated next to the tip.
- **Numbers taken from the Berjano 2006 review (full text read):** RF frequency range 300 kHz–1 MHz
  with tissue treated as purely resistive; a conductivity temperature coefficient of +2 %/°C, used by
  most models and measured below 42 °C; 50 °C as the most frequently used lesion isotherm.
  Arrhenius coefficients for myocardium and blood/tissue conductivities stay `TODO(source)`.
- **Undo:** revert the m27 stage 2 commit.

## 2026-11-04 · m34–m36 stage 4: code labs

- **Three notebooks, Python only** (Part VI has no Octave copies), committed without outputs and run
  in CI by nbmake: `labs/python/m34_lab.ipynb`, `m35_lab.ipynb`, `m36_lab.ipynb`. Each runs in
  seconds; all data are synthetic or come from the course's own models.
- **m35 synthetic task tuned for realism, not ease.** Local and far-field fronts use overlapping
  distance ranges (0.8–4 mm and 2.5–8 mm) so the classifier is good but not perfect (AUC about
  0.93), and the slope feature is measured after a 9-point moving average because noise makes small
  signals look sharp. The leakage part uses 60 synthetic patients with a strong patient signature,
  where a memorizing model (1-NN) gains about 20 points from a record-wise split and logistic
  regression about 5. The patient-level bootstrap uses that clustered task; on part B's task, whose
  labels vary within patients, the two intervals are similar, and the notebook says so.
- **m36 traceability part reads this repository's own tests** with `ast`, and lists two
  requirements verified another way (CI timeout, human review), to show that not every requirement
  is verified by a test.
- **Undo:** revert the stage 4 commit.

## 2026-11-03 · m34–m36 stage 3: demos

- **Defaults for engineering demos.** CLAUDE.md §4 asks for physiologically plausible, cited
  defaults. These demos have few physiological inputs, so they are dimensionless where possible
  (queue load, times in mean service times, score separations) or labeled "illustrative input" in
  their Assumptions. The one real-world default, 8 channels at 1 kHz with 14-bit resolution in
  m34-d2, is cited to the Intracardiac Atrial Fibrillation Database. Typical catheter speeds and
  location update rates stay `TODO(source)` (m34-d3).
- **Leakage demo uses six features.** With two features the 30 synthetic patients overlap and the
  record-wise versus patient-wise gap is small; with six, patient signatures separate and the
  lesson is clear (about 80% versus 60% at the defaults). The gap comes from the patient signature,
  as in the text; the test checks that with no class signal the patient-wise accuracy stays near
  chance while the record-wise accuracy is high.
- **Shared demo math** lives in `demos/m34-common.js`, `m35-common.js` and `m36-common.js`;
  `tests/test_part6_demo_math.py` runs them in Node and compares with the Python models
  (queue departures, data rate, normal CDF, predictive values, binormal AUC, log-gamma and binomial
  CDF, sample sizes, reliability).
- **Standards map (m36)** is a numbered schematic figure inside a badged box, listing only
  requirements whose sources were checked; IEC 60601-1 and IEC 62304 were added to the text with
  their IEC webstore pages. EMC, usability and the EU route are still to come.
- **Undo:** revert the stage 3 commit.

## 2026-11-03 · m34–m36 stage 2: derivations

- **Defaults for the outline questions** (the author chose scikit-learn and left the rest open):
  m34 stops at Little's law and the single-server queue, uses plain Python and synthetic data;
  m35 uses scikit-learn (`scikit-learn>=1.8` in `requirements.txt`), logistic regression in the
  lab, neural networks in text only, synthetic data; m36 covers the US and EU and teaches
  IEC 62304 as in force.
- **Official documents in `references.bib` (needs author approval).** CLAUDE.md §5 asks for a DOI
  or PMID. Regulations, FDA guidances and ISO standards have neither, so they are `@misc` entries
  with the official `url` and the date it was checked (`urldate`). The content test enforces
  this: every other entry still needs a DOI or PMID. ISO 14971's P1·P2 split (Annex C) was
  checked through an FDA presentation that reproduces Figure C.1.
- **One open marker in m36:** the statement that mapping systems are cleared under 21 CFR
  870.1425 with product code DQK is `TODO(source)` until each 510(k) record is checked on the FDA
  database; examples were found only through a secondary index. The EU route and the IEC
  60601-1 / IEC 62304 content wait for their sources (stage 3).
- **Worked numbers come from our code** (for example 59, 93 and 124 units for R = C = 0.95 with
  0, 1 or 2 failures allowed); each quoted value has a test.
- **Branches are stacked** (m34 → m35 → m36), each with a PR against `main`, so merging in order
  avoids conflicts in shared files.
- **Undo:** revert the three stage-2 commits; remove `scikit-learn` from `requirements.txt`.

## 2026-11-03 · m03 stage 6: remaining sections, glossary and formula sheet

- **Front width sourced as a range.** $w = c\,\Delta V/(\pi \max dV_m/dt)$ from @eq-m03-front.
  Human right atrial trabeculae: $\Delta V$ about 95–99 mV and 250–300 V/s [loose2014]; human
  atrial fibres: about 100 V/s [wang1991]. That gives $w$ between about 0.1 and 0.3 mm. The default
  stays 0.3 mm (no change to demos); the assumption text states the range and that it moves
  $a = w + h$ by only 0.2 mm. The arithmetic is checked in `tests/test_m03_unipolar.py`.
- **Literature figures are linked, not copied.** Of the candidate papers, only loose2014 has a
  confirmed CC BY license in PubMed Central's records; the others lack license metadata there, and
  their pages could not be fetched from the authoring environment. Each entry names the figure,
  what it shows (from its caption) and what to compare with this module.
- **Static figures in demo boxes.** The visual summary is a numbered Quarto figure
  (`#fig-m03-filter-chain`, CLAUDE.md §9) inside a `.demo` box, so the badge filter still applies.
  Quarto turns a div with a `fig-` ID into a float and the badge filter does not see it, so the
  badge goes on the outer box. The content test accepts a demo ID or a nested `#fig-mNN-…`.
- **Self-check uses the interview format** (`**S1.**`, answers in `<details>`), checked by the same
  content rule; released modules need at least 5. Numeric answers are checked in tests.
- **Course-wide glossary and formula sheet** at `glossary/index.qmd` and `formula-sheet/index.qmd`,
  linked from the navbar. Tests keep the glossary sorted with module links, and keep each formula
  identical to its module's equation.
- **Guard against Pandoc example lists:** a wrapped line starting with `(@label)` or `@label)`
  becomes a numbered list. A content test now rejects such lines.
- **Undo:** revert the stage 6 commit.

## 2026-11-03 · m03 cheat sheet and interview questions

- **Only results the module already derives.** The cheat sheet restates the module's equations and
  adds a few direct consequences (unipolar peak-to-trough time $2a/c$, a close bipole as
  $-(d\cos\theta/c)\,dU/dt$, the disk's first null at $kr_e \approx 3.83$, the collinear-clique
  limit). Each new statement and each number quoted in an answer has its own test in
  `tests/test_m03_*.py`. The model answers add no new citations: they reuse sources the module
  already cites for the same claims.
- **Answers are hidden by default** in native `<details class="model-answer">` blocks, so readers
  can try a question first. They open with a click, Enter or Space, and need no script.
- **Questions live in the module page** for now. `interview/` in the target layout can later
  collect all modules' questions; a content test already parses the `**Qn.**` + model-answer
  structure, so they can be extracted.
- **New content rule:** questions are numbered in order, each has exactly one model answer, and a
  released module has at least 10.
- **Tables on narrow screens** scroll sideways instead of spilling out of the page.
- **Undo:** remove the two sections' content and the tests named in this entry.

## 2026-11-03 · Move the repo to a project organization

- **Decision (author):** move the repo from the author's personal account to a free GitHub
  organization, `open-ep-mapping-lab`, and rename it `open-ep-mapping-lab.github.io`.
- **Why:** a GitHub Pages address is built from the owner's account name, so the site showed
  the author's username. As an organization site it lives at the root,
  `https://open-ep-mapping-lab.github.io/`, and the code links no longer carry a personal name.
  A custom domain was considered and left for later; it can be added without moving again.
- **One source for addresses:** `_variables.yml` holds the site and repo URLs. Pages link with
  `{{< var repo.url >}}` and `{{< var repo.colab >}}`. A test checks that pages don't hard-code
  the repo and that `_quarto.yml`, `README.md` and the lab notebooks agree with the file.
- **Side effects:** GitHub redirects old repo and git URLs after a transfer, but not the old
  Pages address (`raghavendrasri.github.io/open-ep-mapping-lab/`), which stops working.
- **Undo:** transfer the repo back and restore the old URLs in `_variables.yml`, `README.md`,
  `_quarto.yml` and the notebook's Colab cell.

## 2026-11-02 · Site look (EP theme)

- **One signature element:** a 3-px band of eight discrete colors under the navbar, in the
  red-to-violet order of an isochronal activation map. Everything else stays quiet.
- **Home page hero is computed, not drawn:** a distal unipolar channel and five bipoles along a
  decapolar catheter, on recording-paper grid, generated by `tools/make_hero.py` from the m03
  model (1 m/s, a = 1.3 mm, 2-mm bipoles 7 mm apart). A test fails if it goes stale.
- **Palette:** white paper, slate ink `#1e2b37`, mapping blue `#155e9a` for links and buttons,
  activation red `#b2182b` only for the current page in the sidebar. Status chips on the course
  map (planned, draft, in review, released).
- **Type:** IBM Plex Sans and Plex Mono, self-hosted in `vendor/fonts/ibm-plex/` (SIL Open Font
  License 1.1, license file included). This also removes the Google Fonts request; only
  MathJax still loads from a CDN.
- **Badges in sentence case with a colored dot** instead of all-caps pills.
- **Navbar links stay neutral on the current page.** Quarto highlights the navbar item tied to
  the sidebar (the course map) on every module page, which points at the wrong place; the
  sidebar marks the current page instead.

## 2026-11-02 · m03 code lab

- **Notebook committed without outputs.** CI executes it (nbmake), so outputs never go stale and
  the repo stays small. Colab and Jupyter users see outputs when they run it.
- **Real data is downloaded, not committed (for now).** The outline proposed keeping one iafdb
  record in `data/samples/`, but PhysioNet is not reachable from the authoring environment, so
  the file could not be fetched and checked there. `epml/data.py` downloads it, verifies it
  against PhysioNet's published SHA-256 list, and caches it in `data/cache/` (git-ignored). CI
  sets `EPML_REQUIRE_DATA=1`, so the real-data part must succeed in CI rather than skip, and
  caches the download between runs. Undo: commit the two files to `data/samples/` with a
  `data/registry.json` entry.
- **Octave copy uses anonymous functions, `fprintf` and `assert`** so the same file runs in GNU
  Octave and base MATLAB. CI runs it with figures off.
- **Labs have a 5-minute CI timeout**, enforcing CLAUDE.md §11.

## 2026-11-02 · m03 demos

- **Demo math mirrors the tested Python model.** `demos/m03-common.js` re-implements the
  functions in `labs/python/epml/electrograms.py`; `tests/test_m03_demo_math.py` runs it in Node
  and compares the numbers. Bessel J1 is computed from its integral form (no memorized
  coefficients) and checked against SciPy.
- **One tiny plotting helper, no libraries** (`demos/plot.js`): canvas plots, polar plots, labeled
  sliders, live text readouts. Okabe-Ito colors plus dashes, so curves stay distinguishable
  without color.
- **The render check now exercises every demo:** each must draw, label its canvases and sliders,
  and update its readout when an arrow key moves a slider. This caught a start-up-order bug.
- **Demo defaults and their sources:** c = 1.0 m/s [heil2023], h = 1 mm [riccio2021],
  d = 2 mm [iafdb; riccio2021 for the clique], 1-mm electrode as a 0.5-mm-radius disk [anter2015].
  The front width w = 0.3 mm is **TODO(source)**: it follows from an upstroke near 100 V/s
  [wang1991] only with an action-potential amplitude we have not yet sourced.
- **Far-field demo uses illustrative source strength and timing**, stated as such in its
  Assumptions; only the trend with distance is a claim.

## 2026-11-02 · Course map and placeholder pages

- **Every module has a page from day one.** Unwritten modules get a generated placeholder
  (`status: planned`) showing planned topics, learning paths and planned release, so the whole
  course structure can be shown to people now.
- **`docs/curriculum.md` is the single source of truth.** `tools/sync_curriculum.py` generates the
  placeholder pages, `_sidebar.yml` (loaded through `metadata-files`) and `course-map.qmd`. A test
  fails if they are out of date. Pages with any status other than `planned` are never overwritten.
- **Sidebar parts collapse** (`collapse-level: 1`) so 36 modules stay navigable.

## 2026-11-02 · m03 derivations

- **Arctangent wavefront model.** The rise of V_m across the front is modeled as an arctangent of
  width w. Its slope is a Lorentzian, so the unipolar electrogram has a closed form,
  U(s) = A s / (s² + a²) with a = w + h. This keeps every m03 result exact and testable. A
  tanh or ionic-model front would need numerics. Undo: swap the front model in
  `labs/python/epml/electrograms.py`; the tests compare against independent quadrature, so they
  would show what changes.
- **Omnipole direction = principal axis of the E-field loop.** The published method picks the
  angle whose projection best matches the unipolar derivative (cross-correlation). Both give the
  propagation direction for a plane wave. The text says which one we use.
- **Shared model code lives in `labs/python/epml/`.** Tests, labs and (later) demo data
  generation import the same functions. `tests/conftest.py` adds it to the import path.
- **New content rules:** every numbered equation must be named in a test, and every cited key
  must exist in `references.bib` (`tests/test_content_rules.py`).
- **Bibliography wired into Quarto** (`bibliography: references.bib` in `_quarto.yml`).
  Citations render as author-date with a reference list at the end of each page.

## 2026-11-02 · Publishing the pilot

- **Repo is public, and the site publishes to GitHub Pages** after CI passes on `main`
  (`deploy-pages.yml`, triggered by the CI workflow). A failing check never goes live. Undo:
  set the trigger back to `workflow_dispatch` only.
- **CI moved from Python 3.11 to 3.12.** Dependabot raised the SciPy minimum to 1.18.1, which
  requires Python 3.12, and the install step failed on 3.11. CLAUDE.md §7 now says 3.12+.

## 2026-11-02 · Site skeleton

- **Quarto for the site.** It handles math, cross-references, executed code and search with no
  custom build code. Undo: replace `_quarto.yml` and the `.qmd` front matter.
- **Badges enforced by a Lua filter** (`filters/badges.lua`). A demo without a valid badge stops
  the build, so the rule in CLAUDE.md §4 cannot be skipped by accident.
- **Content rules checked by pytest** (`tests/test_content_rules.py`): section order, front
  matter, demo badges and Assumptions, finished-work checks for released modules, and a doi or
  pmid on every reference.
- **GitHub Pages deploy is manual for now.** The repo is private, and Pages on a free plan needs a
  public repo. CI still builds the site and uploads it as a downloadable preview.
- **MathJax and theme fonts load from CDNs.** The render check reports external failures as
  warnings, not errors. Revisit before v0.1: vendor MathJax into `vendor/` if the site must work
  fully offline.
- **Lab packages added on demand.** `requirements.txt` holds only the build and test tools.
  pyvista, wfdb and openep-py (pinned to a commit) are added with the first lab that uses them.
- **Errata page is written by hand** until there are entries. Generate it from `errata.json`
  once the first correction lands.
