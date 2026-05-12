# Scripts

Utility scripts for the deck builder. None of them are required to use the app —
they're for maintaining the data.

## `crop_cards.py`

Crops a card photo down to its outline (removes the table background) and
normalises every output to the same aspect ratio (0.72, the real Clank!
card ratio) and size (360×500).

Uses OpenCV's GrabCut to separate the card foreground from whatever surface
it was photographed on, then expands the bbox to the target aspect ratio
before resizing.

### Dependencies

```bash
pip3 install --user Pillow numpy opencv-python-headless
```

### Usage

Single image — useful for debugging tricky cards:

```bash
python3 scripts/crop_cards.py path/to/raw_photo.jpg path/to/output.jpg \
  --debug path/to/debug.jpg
```

The debug image shows the original with the detected bbox overlaid, plus the
GrabCut foreground mask.

Batch (a whole directory):

```bash
# Reprocess every card from the backup originals
python3 scripts/crop_cards.py cards-original/ cards/

# Overwrite in place (DANGER: keep a backup first)
python3 scripts/crop_cards.py cards/
```

### When to use it

Whenever a new physical card arrives (e.g. when the Lairs or Underworld
expansion lands by mail):

1. Take a photo of the card, place it in `cards-original/` with the
   correct slug (e.g. `apprentice_thief.jpg`).
2. Run the script targeting `cards/`:
   ```bash
   python3 scripts/crop_cards.py cards-original/apprentice_thief.jpg cards/apprentice_thief.jpg
   ```
3. Update [`../data/cards.json`](../data/cards.json) — set `verified: true`
   and `source: "verified"` for that card.

### Options

| Flag | Default | Meaning |
|---|---|---|
| `--target-ar` | `0.72` | Output aspect ratio (Clank! card ratio is ~0.72) |
| `--size` | `360x500` | Output resolution, or `none` to keep the cropped bbox size |
| `--debug` | (off) | Path for a side-by-side debug image (single-file mode only) |
