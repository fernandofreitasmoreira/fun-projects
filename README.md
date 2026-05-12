# Fun Projects

A personal monorepo of side projects, served as a static site via GitHub Pages.

**Live:** https://fernandofreitasmoreira.github.io/fun-projects/

Each project lives in its own subfolder, is self-contained, and runs as a static page (no build step, no install). The repo root is just a landing page that links into each project.

## Projects

| Project | Status | Description |
|---|---|---|
| [Clank! Catacombs Deck Builder](./clank-catacombs-deckbuilder/) | Active | Interactive card pool, combo analysis, and live deck stats for a custom Clank! Catacombs deck. Supports Catacombs + Adventuring Party + (tentative) Lairs and Underworld. |

## Repo layout

```
fun-projects/
├── index.html                       # Landing page (the "hall of entry")
├── README.md                        # You are here
├── .gitignore
└── clank-catacombs-deckbuilder/     # First project — see its own README
    ├── index.html
    ├── README.md
    ├── cards/                       # Card images (one JPG per card)
    ├── data/                        # Source-of-truth JSON / CSV / XLSX
    └── legacy/                      # Earlier versions kept for reference
```

## Running locally

Open `index.html` in any browser. No server needed. Subprojects work the same way — each has its own `index.html`.

If you prefer a local web server (avoids quirks with `file://` URLs in some browsers):

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Deploying

Hosted on GitHub Pages, served from the `main` branch root. Push to `main` and Pages redeploys automatically.

## Adding a new project

1. Create `your-project-name/` at the repo root.
2. Put an `index.html` inside (and whatever assets it needs).
3. Add a project card to `index.html` at the repo root.
4. Drop a row into the table above.
5. Add a `README.md` inside the project folder.

Keep projects self-contained — vanilla HTML/CSS/JS unless something genuinely needs a build step.

---

Built by [Fernando Moreira](https://github.com/fernandofreitasmoreira).
