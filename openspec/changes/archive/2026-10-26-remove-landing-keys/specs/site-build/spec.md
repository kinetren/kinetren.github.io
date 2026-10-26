# Spec Delta

## MODIFIED Requirements

### Requirement: The site is generated from structure and per-language catalogs
`build.py` SHALL produce `dist/` from `content/structure.toml` (page form: section order,
components, image names, effect names, numbers, guide page order — everything identical
across languages), `content/<lang>.toml` (prose only), the imported guide in
`assets/guide/` and the rest of `assets/`. `dist/` SHALL contain one page per language at
`dist/<lang>/index.html` for every code in `[site] langs`, a root dispatcher
`dist/index.html`, the guide under `dist/docs/`, shared assets under `dist/assets/` (one
content-hashed CSS file, font subsets, images), `sitemap.xml` and `robots.txt`. Nothing in
`dist/` is edited by hand.

#### Scenario: A full build writes every language and the shared assets
- **WHEN** `python3 build.py` runs on the committed sources
- **THEN** it exits 0 and `dist/` contains `index.html`, `en/ ru/ es/ zh-Hans/ ar/` each with `index.html`, `docs/index.html`, `assets/kt.<hash>.css`, `assets/fonts/*.woff`, `sitemap.xml` and `robots.txt`
