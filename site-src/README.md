# RedScribe Docs — site source

The [Astro](https://astro.build) + [Starlight](https://starlight.astro.build)
project that builds the RedScribe documentation site. This is the *editable*
half of `redscribe-docs/` — write markdown here, build it, commit the result
into `../docs/`. See `../README.md` for how the two directories relate and
how to publish via GitHub Pages.

## Project structure

```
site-src/
├── astro.config.mjs       # site title, sidebar nav, outDir (-> ../docs)
├── src/
│   ├── content/docs/      # every page, as markdown — this is what you edit
│   └── styles/custom.css  # RedScribe's color scheme, mapped onto Starlight's tokens
└── public/favicon.svg     # RedScribe's own favicon, reused as-is
```

Starlight turns every `.md`/`.mdx` file under `src/content/docs/` into a
route matching its path (e.g. `src/content/docs/user-guide/findings.md` →
`/user-guide/findings/`). The left-hand navigation is *not* auto-generated
from the file tree — it's the explicit `sidebar` array in
`astro.config.mjs`; add new pages there too, or they won't appear in the nav
(they'll still be reachable by direct URL and search, just not linked).

## Commands

Run from this directory (`site-src/`):

| Command | Action |
|---|---|
| `npm install` | Install dependencies |
| `npm run dev` | Local dev server at `localhost:4321`, with live reload |
| `npm run build` | Build the production site into `../docs/` (see `outDir` in `astro.config.mjs`) |
| `npm run preview` | Serve the built `../docs/` output locally, to sanity-check before committing it |

## Color scheme

`src/styles/custom.css` maps every Starlight design token (`--sl-color-*`)
onto colors from RedScribe's own `COLOR_SCHEME.md` (`brand` = Onyx green as
the primary accent, `bell` = Brick Ember for danger callouts, `navy` =
Ghost White for tip callouts, and `twilight`'s Dim Grey ramp — reused the
same back-to-front way the app's own dark-mode neutral scale reuses it — for
every neutral/gray token in both light and dark mode). If RedScribe's palette
changes, update this file to match rather than inventing new colors here.

## Learn more

[Starlight's own docs](https://starlight.astro.build/) cover components
(`<Aside>`, `<Steps>`, `<Tabs>`, `<Badge>`, `<Card>`), frontmatter options,
and the full theming API in more depth than is worth repeating here.
