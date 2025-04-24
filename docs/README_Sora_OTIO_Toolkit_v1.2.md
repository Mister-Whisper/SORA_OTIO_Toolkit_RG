# Sora OTIO Cascade & Fusion Toolkit — v1.2

A toolkit for decomposing, structuring, and visually blending OpenAI Sora generations inside DaVinci Resolve using OTIO and Fusion.

---

## 📦 Tools Overview

| Tool                          | Role                                                                 |
|-------------------------------|----------------------------------------------------------------------|
| `otio_sora_cascade.py`       | Converts `SORA_OUT` .jsons to OTIO timeline aligned to 0–1 domain   |
| `storyboard_unwrap_to_timeline.py` | Builds OTIO from Sora storyboard JSON with true start/duration logic |
| `otio_to_fusion_comp.py`     | Converts OTIO to Fusion `.comp` with layered blend node flow        |

---

## 🧠 System Design

### Base Timeline Logic
- All operations assume a canonical 0–1 domain across the clip or storyboard
- Durations are mapped to Resolve timeline or Fusion frames (23.976 fps)

### OTIO Roles
- Cascade = Blend-mode logic from base media to variant generations
- Storyboard = Story-sequential structure using `start_time`, `gap_after`

### Fusion Flow
- Each `gen_01` file is loaded as a `Loader`
- Connected into a `Merge` node
- Blend animated using time-based expressions
- Output fully returns to a linear `MediaOut` node

---

## 🔧 Usage Per Tool

### 1️⃣ `otio_sora_cascade.py`
```bash
python otio_sora_cascade.py
```
- Input: Folder of `*.json` from Sora blend metadata
- Output: `sora_cascade.otio`

### 2️⃣ `storyboard_unwrap_to_timeline.py`
```bash
python storyboard_unwrap_to_timeline.py
```
- Input: Single Sora storyboard `.json`
- Output: `storyboard_unwrapped.otio`

### 3️⃣ `otio_to_fusion_comp.py`
```bash
python otio_to_fusion_comp.py
```
- Input: `sora_cascade.otio`
- Output: `sora_comp_v1_2.comp`

---

## 🌀 Fusion Node Layout

```plaintext
MediaIn1
   │
   ▼
 Merge1 ◄── Loader1 (gen_01_A.mp4)
   │
 Merge2 ◄── Loader2 (gen_01_B.mp4)
   │
 Merge3 ◄── Loader3 (gen_01_C.mp4)
   │
MediaOut
```

- Each `Merge.Blend` is time-sliced to fade versions across a domain range
- Blend expression auto-calculated from clip in/out

---

## ✅ Benefits

- Editors can view and compare Sora variants cleanly
- Resolve timelines go from 9+ hour chaos to structured sequences
- Fusion blends are timeline-aligned and X/Y aware

---

## 🧩 Future Work
- Add selector-driven blending
- Generate `.setting` files for Edit tab drag-drop
- Sync to `Resolve Markers` and automate pushback to Sora or GPT review

---

Created by Robert Glickert with OpenAI Assist · Last Updated: v1.2
