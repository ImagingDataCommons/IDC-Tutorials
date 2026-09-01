# Edge-Tile Handling in GrandQC Artifact Segmentation

This note describes, in self-contained form, two strategies for segmenting the
**partial patches at the right and bottom margins of a whole-slide image (WSI)**
during GrandQC's artifact-segmentation stage:

- **Approach A — "stock" tiling.** The strategy in upstream GrandQC's OpenSlide
  inference scripts (`01_WSI_inference_OPENSLIDE_QC/`). This is what
  `grandqc_slide_quality_with_idc.ipynb` runs in **Part 4** (via the
  `fedorov/grandqc` `idc-dicom-fixes` fork, whose fixes are I/O-only and do not
  change algorithm logic).
- **Approach B — "boundary-anchored" tiling.** An alternative that *infers* the
  edge remainder instead of discarding it. `grandqc_slide_quality_with_idc.ipynb`
  implements it in **Part 7** — keeping OpenSlide and every other pipeline choice
  identical to Part 4 — and it is also the strategy used by the rewritten
  in-process `grandqc_qc.py` module in the companion "CLEAN" notebook.

Both approaches use identical models, MPPs (tissue detection at MPP 10, artifact
segmentation at MPP 1.5) and the 7-class scheme. They diverge **only in how the
artifact stage handles the slide edge.**

---

## 1. Why edges are a problem

The artifact model is a fixed **512 × 512** segmentation network run at a target
resolution (MPP 1.5). Each 512 × 512 model patch corresponds to a native
(level-0) window of

```
native_patch = round(model_mpp / slide_mpp * 512)     # "p_s" in GrandQC
```

pixels on a side. The slide is covered by a grid of these native windows. But a
WSI's level-0 width/height is almost never an exact multiple of `native_patch`,
so the **last column and last row of the grid are partial** — they hang off the
right and bottom edges of the slide. The two approaches differ entirely in what
they do with that leftover strip.

Terminology used below:

| Symbol | Meaning |
|---|---|
| `p_s` / `native_patch` | native (level-0) side length of one model patch |
| `w_l0`, `h_l0` | slide width / height at level 0 |
| `MODEL_TILE_SIZE` | 512 (model input side) |
| background class | the label assigned to non-tissue / not-inferred pixels |

---

## 2. Approach A — Stock tiling (floor grid + background-buffer padding)

**Source:** upstream GrandQC `wsi_slide_info.py` and
`wsi_process.py::slide_process_single`.

### 2.1 Grid count is computed with **floor**

```python
# wsi_slide_info.py
patch_n_w_l0 = int(w_l0 / p_s)   # floor: only FULLY-contained columns
patch_n_h_l0 = int(h_l0 / p_s)   # floor: only FULLY-contained rows
```

`int(...)` truncates, so the grid covers **only the patches that fit entirely
inside the slide**. The partial edge column/row is excluded from the loop.

### 2.2 The loop reads only full patches

```python
# wsi_process.py::slide_process_single
for he in range(patch_n_h_l0):
    h = he * p_s + 1
    for wi in range(patch_n_w_l0):
        w = wi * p_s + 1
        ...
        work_patch = slide.read_region((w, h), 0, (p_s, p_s))  # always full p_s x p_s
        work_patch = work_patch.resize((m_p_s, m_p_s), ...)    # -> 512 x 512
        # ... model.predict(...) ...
```

Every read is a complete `p_s × p_s` window, so the edge remainder is never read.

### 2.3 The edge remainder is appended as a **constant background buffer**

After the loop, the leftover strip (whatever lies between `patch_n_* * p_s` and
the true slide extent) is glued on as a block **filled with a constant**, scaled
to model resolution:

```python
# wsi_process.py::slide_process_single  (after the tiling loop)
buffer_right_l  = int((w_l0 - (patch_n_w_l0 * p_s)) * mpp / MPP_MODEL_1)
buffer_bottom_l = int((h_l0 - (patch_n_h_l0 * p_s)) * mpp / MPP_MODEL_1)

buffer_bottom = np.full((buffer_bottom_l, end_image.shape[1]), 0)   # constant fill
temp_image    = np.concatenate((end_image, buffer_bottom), axis=0)
buffer_right  = np.full((temp_image_he, buffer_right_l), 0)          # constant fill
end_image     = np.concatenate((temp_image, buffer_right), axis=1).astype(np.uint8)
```

### 2.4 Net behavior

- The right/bottom margin — **up to one full patch wide** (`native_patch − 1`
  level-0 pixels, i.e. up to 512 model pixels) — is **never shown to the model.**
- It is filled with a constant (background). Any tissue or artifact that lives in
  that margin is silently reported as background/empty.

```
      full patches (inferred)        edge remainder (NOT inferred)
    ┌───────┬───────┬───────┐┌╌╌╌╌╌┐
    │  ✔    │  ✔    │  ✔    ││ 0 0 │   ← right buffer = constant fill
    ├───────┼───────┼───────┤├╌╌╌╌╌┤
    │  ✔    │  ✔    │  ✔    ││ 0 0 │
    └───────┴───────┴───────┘└╌╌╌╌╌┘
    ┌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐ 0 0     ← bottom buffer = constant fill
    └╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘
```

---

## 3. Approach B — Boundary-anchored tiling (ceil grid + back-shifted full patch)

**Source:** implemented in Part 7 of `grandqc_slide_quality_with_idc.ipynb`
(`run_artifact_anchored`), mirroring the CLEAN notebook's
`grandqc_qc.py::_run_artifact_detection` / `_predict_artifact_patch`.

### 3.1 Grid count is computed with **ceil**

```python
native_patch = int(artifact_mpp / slide_mpp * MODEL_TILE_SIZE)
patch_n_w = math.ceil(slide_width  / native_patch)   # ceil: COVER the edge
patch_n_h = math.ceil(slide_height / native_patch)   # ceil: COVER the edge
```

`math.ceil` guarantees the grid **covers the whole slide**, including a final
column/row that overhangs the edge.

### 3.2 Edge cells are read by **shifting the window back inside the slide**

For each grid cell at nominal origin `(x0, y0) = (wi·native_patch, he·native_patch)`,
the read origin is anchored so a **complete** `native_patch × native_patch` block
is always read — at the far edge the window slides backwards to end exactly at the
slide boundary (overlapping its neighbor) instead of being padded:

```python
def _anchored_start(grid_origin, window, extent):
    # far edge -> anchor at (extent - window) instead of padding the partial tile
    return max(0, min(grid_origin, extent - window))

read_x = _anchored_start(x0, native_patch, slide_width)     # shifts back at right edge
read_y = _anchored_start(y0, native_patch, slide_height)    # shifts back at bottom edge

region = slide.read_region((read_x, read_y), 0, (native_patch, native_patch))  # full window
tile   = region.resize((MODEL_TILE_SIZE, MODEL_TILE_SIZE), Image.Resampling.LANCZOS)
raw    = argmax(model.predict(tile))
```

### 3.3 The prediction is **realigned back to the grid cell**

Because the read window was shifted, its prediction is offset back so only the
portion belonging to this grid cell is kept; anything past the slide edge is set
to background (so the overlap with the previous tile is not double-written):

```python
off_x = round((x0 - read_x) / native_patch * MODEL_TILE_SIZE)
off_y = round((y0 - read_y) / native_patch * MODEL_TILE_SIZE)
if off_x or off_y:
    aligned = np.full((MODEL_TILE_SIZE, MODEL_TILE_SIZE), BACKGROUND, np.uint8)
    aligned[:MODEL_TILE_SIZE - off_y, :MODEL_TILE_SIZE - off_x] = raw[off_y:, off_x:]
    raw = aligned
```

Finally the assembled mask is cropped back to the true slide extent at model
resolution.

### 3.4 Net behavior

- **Every pixel of the slide, including the right/bottom margin, is classified by
  the model** at the correct scale.
- The edge is inferred from a full, unstretched `native_patch` window (read from
  a shifted origin), not from a thin strip stretched across 512 px and not from a
  constant fill.

```
      full patches (inferred)     edge cell = full patch, read origin shifted back
    ┌───────┬───────┬───────┬──────┐
    │  ✔    │  ✔    │  ✔    │  ✔   │   ← last column read from x = width - native_patch
    ├───────┼───────┼───────┼──────┤     (overlaps neighbor; realigned + cropped)
    │  ✔    │  ✔    │  ✔    │  ✔   │
    ├───────┼───────┼───────┼──────┤
    │  ✔    │  ✔    │  ✔    │  ✔   │   ← last row read from y = height - native_patch
    └───────┴───────┴───────┴──────┘
```

### 3.5 The overlap strip is inferred twice, but written once

The back-shifted edge window overlaps its interior neighbor. Those slide pixels
are therefore pushed through the model twice, and — because a segmentation CNN's
label for a pixel depends on its surrounding receptive field, which differs
between the two placements — the **two raw predictions for the overlap can
differ.** The realignment in §3.3 resolves this deterministically: the `off_x` /
`off_y` crop **discards** the edge window's prediction for the overlap and keeps
only the genuinely-new edge strip `[x0, width)`. Each output pixel is written by
exactly one grid cell (the overlap keeps the interior tile's label), so the final
mask is single-valued — the only cost is the redundant inference on the overlap.

---

## 4. Side-by-side comparison

| | **A — Stock (Part 4)** | **B — Boundary-anchored (Part 7)** |
|---|---|---|
| Grid count | `int(w/p_s)` — **floor** | `ceil(w/native_patch)` — **ceil** |
| Edge column/row | dropped from the loop | included in the loop |
| Edge read | not read | full `native_patch` window from a **back-shifted** origin |
| Edge fill | constant **background buffer** | **model prediction** (realigned, then cropped) |
| Edge pixels inferred? | **No** | **Yes** |
| Overlap handling | n/a (no edge read) | inferred twice, but only the interior copy is kept (§3.5) |

---

## 5. Worked example

Slide 20,000 × 15,000 px at level 0, artifact MPP 1.5 on a 0.5 MPP slide
⇒ `native_patch = round(1.5/0.5 × 512) = 1536`.

- **Approach A:** `patch_n_w = int(20000/1536) = 13`, `patch_n_h = int(15000/1536) = 9`.
  Inferred region = `13·1536 × 9·1536 = 19968 × 13824`. The remaining
  **32-px-wide right strip and 1176-px-tall bottom strip are filled with
  background** — never seen by the model.
- **Approach B:** `patch_n_w = ceil(20000/1536) = 14`, `patch_n_h = ceil(15000/1536) = 10`.
  The 14th column is read from `x = 20000 − 1536 = 18464` and the 10th row from
  `y = 15000 − 1536 = 13464`, so those full windows are inferred and realigned;
  **the whole 20000 × 15000 extent is classified.**

(Approach A's 32-px strip is negligible, but a bottom strip up to `native_patch−1`
= 1535 level-0 px — here 1176 px — is a visible band of missed tissue.)

---

## 6. Practical consequence

The two approaches produce **identical masks in the slide interior** but
**different masks along the right and bottom margins** on any slide whose
dimensions are not exact multiples of `native_patch` (i.e. essentially all real
slides):

- Approach A leaves a margin — up to nearly one full patch tall/wide — as
  **background**, so tissue and artifacts there are missed.
- Approach B **classifies that margin** using a full-resolution, boundary-anchored
  patch.

Part 7 of `grandqc_slide_quality_with_idc.ipynb` implements Approach B on top of
the exact Part 4 pipeline (same OpenSlide reader, model, MPP, tissue masks, and
class labels), so the only variable is the edge handling. The side-by-side
comparison there shows the interior masks agreeing pixel-for-pixel while the
edge band diverges — Approach A background vs. Approach B classified tissue.

> **Note on the tissue-detection stage.** This divergence is confined to the
> **artifact-segmentation** stage. GrandQC's earlier **tissue-detection** stage
> already anchors its edge tiles (it crops the last tile at `width−512` /
> `height−512` rather than padding), so both approaches share the same
> tissue-detection edge behavior; only the artifact stage differs.
