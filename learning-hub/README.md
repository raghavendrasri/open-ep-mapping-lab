# Learning Hub

A self-contained, interactive orientation page for the course, published at `learning-hub/index.html` and linked
from the navbar as "Learning hub".

- `source/Electrophysiology_Mapping_System.html`: the author's original page, made with Muse. The embedded raster
  hero image has been removed from this copy.
- `source/make_hero_svg.py` and `source/hero.svg`: the original schematic drawing that replaces the hero image.
- `index.html`: the published page. **Do not edit it by hand.** Change the source or
  `tools/build_learning_hub.py`, then run:

```
python tools/build_learning_hub.py
pytest -q tests/test_learning_hub.py
```

The build script applies named, exact-match edits that bring the page in line with CLAUDE.md: self-hosted fonts,
citations from `references.bib`, "unverified" tags for product facts that have no source yet (see `errata.json`,
E2), and description instead of clinical advice. Status: draft, pending clinical review.
