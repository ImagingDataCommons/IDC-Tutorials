# GrandQC + IDC: Notes on Inference Resolution

Supplementary notes for [`grandqc_slide_quality_with_idc.ipynb`](grandqc_slide_quality_with_idc.ipynb).

This document explains, for the GrandQC inference scripts in
`grandqc/01_WSI_inference_OPENSLIDE_QC/`, **what resolution the model runs at,
where that is controlled, and how the per-slide microns-per-pixel (MPP) value is
determined** when slides are read from NCI Imaging Data Commons (IDC) as DICOM.

---

## Two distinct resolutions

There are two separate resolution concepts in the pipeline. They are easy to
conflate but are set in different places.

| Resolution concept | Value (this tutorial) | Where it is set |
|---|---|---|
| **Model working resolution** (MPP the network "sees") | `1.5` µm/px (≈ 7× objective) | `--mpp_model` CLI flag → `MPP_MODEL` in `main.py` |
| **Tissue-detection resolution** (Step 1) | `10` µm/px | hardcoded in `wsi_tis_detect.py` |
| **Model input tile size** | `512 × 512` px | `M_P_S_MODEL = 512`, hardcoded in `main.py` |
| **Native read size per tile** | `mpp_model / mpp × 512` px (level 0) | computed in `wsi_slide_info.py:slide_info()` |

The model **never** runs at the slide's native 20×/40× magnification. The tissue
detector runs coarsest (MPP 10); the artifact model runs at MPP 1.5.

---

## 1. Model working resolution — `--mpp_model`

The artifact-segmentation step (notebook Part 4.2) is invoked as:

```python
subprocess.run([sys.executable, "main.py",
    "--slide_folder", slide_dir_abs,
    "--output_dir",   output_dir_abs,
    "--mpp_model",    "1.5",
    "--create_geojson", "Y"], cwd=scripts_abs)
```

`--mpp_model` sets `MPP_MODEL` in `main.py` and does two things:

1. **Selects the model weights** — only three values are valid:

   | `--mpp_model` | weights file |
   |---|---|
   | `1.0` | `GrandQC_MPP1.pth` |
   | `1.5` | `GrandQC_MPP15.pth` |
   | `2.0` | `GrandQC_MPP2.pth` |

   Any other value raises `Exception("mpp of the model can only be 1.0, 1.5, 2.0")`.

2. **Sets the magnification slides are read at** (see §3).

> **To change the inference resolution** you must set `--mpp_model` to `1.0` or
> `2.0` **and** download the matching weights. The notebook's model-download cell
> (Part 2.2) only fetches `GrandQC_MPP15.pth`, so switching MPP requires adding the
> corresponding Zenodo download.

---

## 2. Model input tile size — fixed at 512×512

Hardcoded in `main.py`; not a CLI flag:

```python
M_P_S_MODEL = 512   # the network always receives 512×512 px tiles
```

Every tile is downsampled to 512×512 before inference (§3). Changing this would
require retraining and should not be altered.

---

## 3. How the two combine

`wsi_slide_info.py:slide_info()` converts the model MPP into a patch size measured
in the slide's **native level-0 pixels**:

```python
mpp = float(slide.properties["openslide.mpp-x"])   # slide's native MPP
p_s = int(mpp_model / mpp * m_p_s)                  # patch size in level-0 px
```

Then `wsi_process.py:slide_process_single()` reads that region at full resolution
and downsamples it to the fixed model input size:

```python
work_patch = slide.read_region((w, h), 0, (p_s, p_s))                  # read p_s × p_s from level 0
work_patch = work_patch.resize((m_p_s, m_p_s), Image.Resampling.LANCZOS)  # → 512×512
predictions = model.predict(x_tensor)                                  # inference at 512×512 (= MPP 1.5)
```

**Worked example** — a 40× TCGA-BRCA slide with native MPP ≈ `0.2485`, `mpp_model = 1.5`:

```
p_s = int(1.5 / 0.2485 * 512) = int(3091.0) = 3091 px   # read from level 0
     → downsampled to 512×512 → fed to the network
```

The downsampling makes the effective resolution seen by the network MPP 1.5,
regardless of whether the slide was scanned at 20× or 40×.

---

## 4. How MPP is determined

MPP is **read from OpenSlide**, not computed. The only place it is obtained is the
single line in `wsi_slide_info.py:slide_info()`:

```python
mpp = float(slide.properties["openslide.mpp-x"])
```

Key points:

- It is **read, not derived** from objective power. Only the X axis is used
  (square pixels are assumed; `mpp-y` is ignored).
- **No fallback for MPP.** Note the asymmetry in the same function — objective
  power has a fallback, MPP does not:

  ```python
  try:
      obj_power = slide.properties["openslide.objective-power"]
  except:
      obj_power = 99            # objective power: falls back to 99

  mpp = float(slide.properties["openslide.mpp-x"])   # MPP: no fallback
  ```

  If `openslide.mpp-x` is missing/`None`, `float(...)` raises. With the
  fail-loud error handling in the `idc-dicom-fixes` fork branch, this is caught
  and reported per slide (with a non-zero exit) rather than silently mis-scaling.
- `openslide.mpp-x` is the **single point of failure** for scaling any new slide:
  if it is wrong or absent, `p_s` is sized wrong and the model sees the slide at
  the wrong scale.

### For IDC DICOM slides specifically

OpenSlide's DICOM driver (added in OpenSlide 4.0.0) populates `openslide.mpp-x`
from the DICOM `PixelSpacing` attribute (mm → µm).

**Verified empirically** on IDC slide `TCGA-A7-A26J-01B-02-BS2`
(the 9.1 MB series used in the notebook), downloaded with `idc-index` and opened
with OpenSlide 4.0.1:

```
openslide.vendor          = dicom
openslide.mpp-x           = 0.24850000000000003
openslide.mpp-y           = 0.24850000000000003
openslide.objective-power = 40
```

The raw DICOM source attribute is exposed on the same slide:

```
dicom.SharedFunctionalGroupsSequence[0].PixelMeasuresSequence[0].PixelSpacing[0] = .0002485   # mm
```

and `0.0002485 mm × 1000 = 0.2485 µm/px`, which matches `openslide.mpp-x` exactly.
This also matches the `pixel_spacing_mm = 0.00025` shown in the notebook's
metadata query (the 2-significant-figure rounded form).

The notebook's Part 3.3 verification cell already surfaces this value with
`slide.properties.get("openslide.mpp-x", "N/A")`, so you can inspect MPP per slide
before running Step 2.

---

## Quick reference: changing resolution safely

1. Pick a supported MPP: `1.0`, `1.5`, or `2.0`.
2. Download the matching weights from Zenodo into `models/qc/`
   (`GrandQC_MPP1.pth` / `GrandQC_MPP15.pth` / `GrandQC_MPP2.pth`).
3. Pass it via `--mpp_model` in the Step 2 `subprocess.run` call.
4. Leave `M_P_S_MODEL = 512` unchanged.
5. Confirm each slide reports a valid `openslide.mpp-x` (Part 3.3) before running —
   it has no fallback.
