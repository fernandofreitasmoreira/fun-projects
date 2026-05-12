#!/usr/bin/env python3
"""
Crop a Clank! card down to its outline using GrabCut.

GrabCut is OpenCV's standard interactive foreground extraction algorithm.
Initialized with a rectangle, it iteratively separates foreground (the card)
from background (the table) using color statistics. Robust to uneven lighting
and varied table texture — exactly the failure modes the simpler approaches
ran into.

Procedure:
  1. Assume the card occupies roughly the central 90% of the photo —
     initialise GrabCut with that rectangle.
  2. Run 5 iterations.
  3. Take the foreground mask, fill any holes, pick the largest blob.
  4. Crop with a small inset to drop the printed black frame line.
"""
import sys, cv2, numpy as np, pathlib, json

def crop_card(in_path, out_path, debug_path=None,
              init_margin=0.04, iters=5, inset=0,
              target_ar=0.72, target_size=(360, 500)):
    img = cv2.imread(in_path)
    if img is None: raise FileNotFoundError(in_path)
    H, W = img.shape[:2]
    img_area = H * W

    # 1. Init rectangle: the entire image minus a small outer margin.
    #    GrabCut treats pixels outside the rect as definite background.
    m = int(round(init_margin * min(W, H)))
    rect = (m, m, W - 2 * m, H - 2 * m)

    mask = np.zeros((H, W), np.uint8)
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(img, mask, rect, bgd, fgd, iters, cv2.GC_INIT_WITH_RECT)

    # 2. Build a binary mask: foreground = 1 / 3 (definite + probable FG)
    fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)

    # 3. Fill holes inside the card (text white space etc.)
    closed = cv2.morphologyEx(
        fg, cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)),
        iterations=2)

    # 4. Bbox of ALL foreground pixels (not just the largest blob — small
    # disconnected pieces near corners belong to the card too).
    ys, xs = np.where(closed > 0)
    if len(xs) == 0: raise RuntimeError(f"{in_path}: GrabCut found no foreground")
    x = int(xs.min()); x_end = int(xs.max()) + 1
    y = int(ys.min()); y_end = int(ys.max()) + 1
    w = x_end - x; h = y_end - y
    area_frac = (w * h) / img_area

    # 5. Optional inset (default 0 keeps the card frame; >0 trims the frame)
    x_i = max(0, x + inset)
    y_i = max(0, y + inset)
    w_i = max(1, w - 2 * inset)
    h_i = max(1, h - 2 * inset)

    # 6. Normalise to target aspect ratio by EXPANDING the bbox
    # (never contract — that would clip card content).
    cur_ar = w_i / h_i
    if cur_ar < target_ar:
        # Card bbox is too narrow → expand width
        desired_w = int(round(h_i * target_ar))
        cx = x_i + w_i / 2
        new_x = int(round(cx - desired_w / 2))
        new_x = max(0, min(new_x, W - desired_w))
        if new_x + desired_w > W:
            # Image isn't wide enough; expand height instead (contract h to match)
            desired_h = int(round(w_i / target_ar))
            cy = y_i + h_i / 2
            new_y = int(round(cy - desired_h / 2))
            new_y = max(0, min(new_y, H - desired_h))
            x_i, y_i, h_i = new_x, new_y, min(desired_h, H - new_y)
        else:
            x_i, w_i = new_x, desired_w
    elif cur_ar > target_ar:
        # Card bbox is too wide → expand height
        desired_h = int(round(w_i / target_ar))
        cy = y_i + h_i / 2
        new_y = int(round(cy - desired_h / 2))
        new_y = max(0, min(new_y, H - desired_h))
        if new_y + desired_h > H:
            desired_w = int(round(h_i * target_ar))
            cx = x_i + w_i / 2
            new_x = int(round(cx - desired_w / 2))
            new_x = max(0, min(new_x, W - desired_w))
            x_i, w_i = new_x, min(desired_w, W - new_x)
        else:
            y_i, h_i = new_y, desired_h

    cropped = img[y_i:y_i + h_i, x_i:x_i + w_i]

    # 7. Resize to a consistent output size (Lanczos for sharpness)
    if target_size:
        cropped = cv2.resize(cropped, target_size, interpolation=cv2.INTER_LANCZOS4)

    cv2.imwrite(out_path, cropped, [cv2.IMWRITE_JPEG_QUALITY, 92])

    info = {
        "in": in_path, "out": out_path,
        "src_size": [W, H],
        "bbox_raw": [int(x), int(y), int(w), int(h)],
        "bbox_inset": [x_i, y_i, w_i, h_i],
        "out_size": [cropped.shape[1], cropped.shape[0]],
        "aspect_ratio": round(w / h, 3),
        "area_frac": round(area_frac, 3),
    }

    if debug_path:
        dbg = img.copy()
        cv2.rectangle(dbg, (int(x), int(y)), (int(x + w), int(y + h)), (0, 200, 255), 2)
        cv2.rectangle(dbg, (x_i, y_i), (x_i + w_i, y_i + h_i), (0, 255, 0), 3)
        side = np.hstack([
            dbg,
            cv2.cvtColor(fg, cv2.COLOR_GRAY2BGR),
            cv2.cvtColor(closed, cv2.COLOR_GRAY2BGR),
        ])
        cv2.imwrite(debug_path, side, [cv2.IMWRITE_JPEG_QUALITY, 80])

    return info


def batch(src_dir, dst_dir, ext="*.jpg"):
    """Process every image in src_dir, writing cropped versions to dst_dir."""
    import time
    src_dir = pathlib.Path(src_dir); dst_dir = pathlib.Path(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(src_dir.glob(ext))
    if not files:
        print(f"No {ext} files in {src_dir}"); return
    print(f"Processing {len(files)} files: {src_dir} → {dst_dir}")
    t0 = time.time()
    ok = errors = 0
    for i, f in enumerate(files, 1):
        try:
            crop_card(str(f), str(dst_dir / f.name))
            ok += 1
        except Exception as e:
            errors += 1
            print(f"  ! {f.name}: {e}")
        if i % 20 == 0 or i == len(files):
            print(f"  [{i:3}/{len(files)}] {time.time() - t0:.1f}s elapsed")
    print(f"Done in {time.time() - t0:.1f}s — {ok} ok, {errors} errors")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Crop Clank! card photos to their outline.")
    p.add_argument("src", help="Source image file OR directory")
    p.add_argument("dst", nargs="?", help="Output image file or directory (defaults to overwriting src)")
    p.add_argument("--debug", help="Write a side-by-side debug image here (single-file mode only)")
    p.add_argument("--target-ar", type=float, default=0.72)
    p.add_argument("--size", default="360x500", help="WxH output size (e.g. 360x500), or 'none' to keep native bbox size")
    args = p.parse_args()

    target_size = None
    if args.size and args.size != "none":
        w, h = map(int, args.size.lower().split("x"))
        target_size = (w, h)

    src = pathlib.Path(args.src)
    if src.is_dir():
        dst = pathlib.Path(args.dst) if args.dst else src
        batch(src, dst)
    else:
        dst = args.dst or str(src)
        info = crop_card(str(src), str(dst), args.debug,
                         target_ar=args.target_ar, target_size=target_size)
        print(json.dumps(info, indent=2))
