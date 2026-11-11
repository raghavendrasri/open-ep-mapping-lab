# Decisions log

Non-trivial choices, newest first. Each entry: date, decision, why, and how to undo it.

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
