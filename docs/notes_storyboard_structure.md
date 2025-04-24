Yes — for **Sora Storyboard outputs**, you should absolutely apply the **same compound/unwrap cascade logic** as with blends, using the `0–1` X-domain model and ripple/split operations. Here's how it aligns:

---

## ✅ Sora Storyboard = Canonical 0–1 Timeline

From `storyboard_get_data_fast_CANON_LOCKED.js`, we know:

- Each storyboard clip has:
  - `start_time`, `end_time` (in seconds)
  - `overall_duration` of the full storyboard
- These are already **normalized within that storyboard timeline**

---

## 🧩 UNWRAP LOGIC FOR STORYBOARDS

Think of this like:

> Storyboard timeline = **master compound (0–1 space)**
> Each clip inside = like a blend domain
> OTIO or Resolve view = unwrap into full timeline with ripple and stacking

---

### 🎬 Timeline Rules (Just like your Resolve screenshots):

- Compound clip = Sora storyboard (whole generation timeline)
- Opened contents:
  - Each prompt, video, or hallucination = **placed by `start_time`**
  - If clips are **longer than the segment they appear in** → **they overflow**, require:
    - **Split**
    - **Ripple forward**
    - **New track allocation**

✅ Same as the blend logic you just built into `otio_sora_cascade.py`.

---

## 🔧 Minor Difference: Source Fields

- Blends use:
  ```json
  "clip_section_start": 0.3,
  "clip_section_end": 0.6,
  "duration": 10.0
  ```

- Storyboards use:
  ```json
  "start_time": 2.0,
  "end_time": 4.5,
  "duration": 2.5
  ```

Same logic, just **no need to normalize** — values are already in-place.

---

## ✅ TL;DR

| Concept                     | Blends                        | Storyboards                   |
|----------------------------|-------------------------------|-------------------------------|
| Canonical range            | 0.00 → 1.00                   | 0.00 → `overall_duration`     |
| Decomposable in Resolve    | ✅ Compound Unwrap            | ✅ Compound Unwrap            |
| Needs ripple/split         | ✅ Yes                        | ✅ Yes                        |
| OTIO-compatible            | ✅ Your script works w/ mods  | ✅ With minor input patch     |

---

### ✅ RECOMMENDED:

1. Use the same `TimelineBuilder` class
2. Accept `start_time`, `duration`, `gap_after`
3. Build `storyboard_unwrap_to_timeline.py` to:
   - Read the canonical JSON from your extraction tool
   - Insert clips at `start_time`, duration = `duration`
   - Handle ripple/split if needed
   - Stack Y variants into layered tracks

Want me to generate that script (`storyboard_unwrap_to_timeline.py`) with your verified cascade logic next?
