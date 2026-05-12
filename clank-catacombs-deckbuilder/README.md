# Clank! Catacombs — Custom Deck Builder

An interactive, single-page tool for designing and analyzing a custom card pool for the board game [Clank! Catacombs](https://renegadegamestudios.com/clank-catacombs/). It currently covers the **Catacombs** base game, the **Adventuring Party** pack, and tentative entries for the upcoming **Lairs** and **Underworld** expansions.

**Open it:** [index.html](./index.html) — runs entirely in the browser, no install, no build.

![Clank Catacombs Deck Builder screenshot placeholder]()

## Features

- **Card Pool** — browse all 138 cards with filters (set, type, cost, dragon attack, combo cluster, trash type, verification status) and sorts (set, name, cost, VP, quantity, combo score).
- **My Deck** *(new)* — click *+ Deck* on any card to add it, ⊕/⊖ to adjust quantity, autosaves to `localStorage`. Live stats panel shows totals, resources, type breakdown, cost curve, dragon ratio, and combo participation. Export / Import / Copy as JSON.
- **Statistical Analysis** — type distribution, cost histogram, sword cost (monsters), dragon-attack % per set, top mechanics, per-set type breakdown, resource totals — all rendered as inline SVG.
- **Combos & Synergies** — cluster health (providers vs triggers), cluster-count distribution, top combo cards, trash-policy breakdown, orphan cards.
- **Targets vs Pool** — compares the current pool against the exact 100-card retail Catacombs box across type ratios, dragon %, trash, draw, resource densities, and projected totals at a 100-card deck size.

## How to run

Just open [`index.html`](./index.html) in a browser. Card images load from `./cards/`, the data is embedded in the HTML so it works on `file://` too. For full URL ergonomics (image hover, etc.), you can also serve it locally:

```bash
python3 -m http.server 8000
open http://localhost:8000
```

## Repo layout

```
clank-catacombs-deckbuilder/
├── index.html                  # The whole app — CSS, JS, and data embedded
├── README.md                   # You are here
├── cards/                      # 93 card images (one JPG per card)
│   ├── empurror.jpg
│   ├── ape_lord_phantasm.jpg
│   └── …
├── data/                       # Source-of-truth data files
│   ├── cards.json              # Clean unified card pool (138 cards) — the JSON the app uses
│   ├── master_pool.json        # Earlier export (incl. sets_included / sets_pending metadata)
│   ├── card_to_image.json      # Card name → image path lookup
│   ├── catacombs_dungeon_deck.csv   # Verified Catacombs base (108 cards) — primary truth
│   ├── ap_cards.json           # Adventuring Party expansion (25 cards)
│   ├── extracted_cards.json    # Underworld cards extracted from photos via OCR
│   ├── metrics.json            # Precomputed summary metrics
│   └── Clank_Master_Pool_v1.xlsx
└── legacy/                     # Earlier exports kept for reference (charts, dataset, original HTMLs)
```

## Data model

Each card in [`data/cards.json`](./data/cards.json) follows this shape:

```jsonc
{
  "name": "Empurror",
  "set": "Catacombs",                     // Catacombs | Adventure | Lairs | Underworld
  "type": "Companion",                    // Companion | Monster | Device | Gem | Other
  "cost": 1,                              // null for starter cards / monsters use sword cost
  "costNum": 1,                           // numeric copy for sorting
  "isMonster": false,
  "skill": 0,
  "swords": 0,
  "boots": 0,
  "vp": 1,
  "text": "Choose one (or all three, if you have an artifact)…",
  "acquire": "",                          // text triggered when bought
  "arriveDanger": "",                     // text on arrival or as a danger card
  "dragonAttack": false,
  "quantity": 1,                          // copies of this card in the physical box
  "mechanics": ["Clank-", "Crystal-Cave", "Artifact"],   // free-form tags
  "image": "cards/empurror.jpg",
  "flavor": "",
  "combo": {
    "provides":    ["Companion"],         // resources this card enables for others
    "triggers":    ["Artifact"],          // resources this card reads from to combo
    "interactive": [],                    // React / Arrive-Choice / etc.
    "trashTags":   [],                    // Active-Trash / Self-Trash / Trash-Payoff
    "clusters":    ["Artifact", "Companion-Chain", "Position-Cave"]
  },
  "comboScore": 9,                        // 2×clusters + 3×triggers + 2×interactive + 2×trashPayoff + 2×activeTrash − 1×selfTrash
  "verified": true,                       // false = pending physical verification
  "source": "verified"                    // verified | author-v1.2 | image-extracted
}
```

### Combo score formula

```
comboScore = 2 × len(clusters)
           + 3 × len(triggers)
           + 2 × len(interactive)
           + 2 × count(trashTags == "Trash-Payoff")
           + 2 × count(trashTags == "Active-Trash")
           − 1 × count(trashTags == "Self-Trash")
```

Higher score = more combo potential. The app sorts and highlights cards with `comboScore > 5`.

### Verification status

- **`verified: true`** — card data confirmed against the physical card.
- **`verified: false`** — tentative entry, marked with the *tentative* badge in the UI. Currently 22 cards from the Lairs and Underworld expansions are tentative, pending the physical boxes arriving by mail.

When the expansions arrive:

1. Photograph the cards.
2. Update entries in [`data/cards.json`](./data/cards.json): set `"verified": true` and `"source": "verified"`.
3. Add the physical card images to `./cards/` (lowercase, underscore-separated, e.g. `apprentice_thief.jpg`).
4. The pending banner and tentative badges in the UI clear automatically.

## My Deck (persistence)

Cards added to *My Deck* are stored in `localStorage` under the key `clank-catacombs-deck-v1`:

```json
{
  "name": "My Clank deck",
  "cards": { "Empurror": 1, "Skeletal Ape": 2 },
  "updated": "2026-05-12T11:34:00.000Z"
}
```

- **Auto-save** — every change persists immediately.
- **Export JSON** — downloads the deck as a file (e.g. `my_clank_deck.json`).
- **Import JSON** — load a deck back. Unknown card names trigger a confirmation before they're dropped.
- **Copy** — copies the deck JSON to the clipboard for quick sharing.
- **Clear** — empties the deck (with a confirm dialog).

Keyboard shortcuts in the card modal: `+` / `-` to adjust quantity, `Esc` to close.

## Combo clusters

Cards group into combo clusters based on the resources they read from or provide. The full list (defined in `index.html`, `CLUSTERS_INFO`) includes:

- **Companion-Chain** — cards that need other companions in play.
- **Artifact**, **Crystal-Cave**, **Market**, **Crypt**, **Cave** — positional clusters that reward being in or having visited a specific room type.
- **Burgle-Removal** — cards that let you trash starter Burgles for deck thinning.
- **Trash-Payoff** — cards that trigger when something is trashed.
- **Draw-Engine**, **Tutor**, **Discount**, **Skill-Burst**, **Combat-Burst** — utility clusters.

A cluster is **active** when it has both *providers* and *triggers* in the pool; otherwise it's *passive* or *dead*. The Combos tab shows cluster health at a glance.

## Roadmap

- [ ] Photograph the **Lairs** expansion when it arrives, promote tentative cards to verified.
- [ ] Photograph the **Underworld** expansion (the 5 remaining tentatives), add any missing cards.
- [ ] Integrate the older `legacy/clank_catacombs_analysis.original.html` as a *Catacombs Base* tab (cuts list, design principles, gaps).
- [ ] Per-deck snapshot / version history.
- [ ] Shareable deck URL (encode deck in URL hash for easy sharing without a server).

## Credits

Clank! is © Renegade Games / Dire Wolf Digital. All card text and images are © their respective owners. This tool is a fan project for personal use.
