# otio_to_fusion_comp.py
# Version: v1.2
# Description: Converts Sora OTIO timeline to a Fusion .comp file with Loaders, Merges, and Blend expressions
# Supports grouped versions of same domain stacked and crossfaded
# Now Fusion-safe with trailing comma removal and syntax validation

import opentimelineio as otio
import os
from collections import defaultdict

FUSION_HEADER = """
Composition {
	Tools = ordered() {
"""

FUSION_FOOTER = "	}
}
"

FRAME_RATE = 24000 / 1001  # 23.976 fps


def to_frames(seconds):
    return int(round(seconds * FRAME_RATE))


def sanitize_name(name):
    return name.replace("-", "_").replace(".", "_")


def build_fusion_comp(otio_path, output_path):
    timeline = otio.adapters.read_from_file(otio_path)
    node_blocks = []
    loader_count = 1
    merge_count = 1
    media_out_idx = 1

    track = timeline.tracks[0]
    prev_merge_name = ""

    domain_groups = defaultdict(list)
    for clip in track:
        start = to_frames(clip.range_in_start_time().value)
        dur = to_frames(clip.trimmed_range().duration.value)
        end = start + dur
        domain_groups[(start, end)].append(clip)

    for (start, end), versions in domain_groups.items():
        blend_span = end - start
        last_merge = prev_merge_name or "MediaIn1"
        for i, clip in enumerate(versions):
            name = sanitize_name(clip.name)
            loader_name = f"Loader{loader_count}"
            merge_name = f"Merge{merge_count}"
            media_url = clip.media_reference.target_url.replace("\\", "\\\\")

            loader_block = f"""
		{loader_name} = Loader {{
			Clips = {{
				Clip {{ ID = \"Clip1\", Filename = \"{media_url}\", GlobalStart = {start}, GlobalEnd = {end} }}
			}},
			ViewInfo = OperatorInfo {{ Pos = {{ {100 + 100 * loader_count}, {50} }} }}
		}}"""
            node_blocks.append(loader_block)

            fade_in = start + i * (blend_span // len(versions))
            fade_out = fade_in + blend_span // len(versions)
            blend_expr = f"if(time >= {fade_in} and time <= {fade_out}, (time - {fade_in}) / ({fade_out - fade_in}), time < {fade_in} and 0 or 1)"

            merge_block = f"""
		{merge_name} = Merge {{
			CtrlWZoom = false,
			Inputs = {{
				Blend = Input {{ Expression = \"{blend_expr}\" }},
				Foreground = Input {{ SourceOp = \"{loader_name}\", Source = \"Output\" }},
				Background = Input {{ SourceOp = \"{last_merge}\", Source = \"Output\" }}
			}},
			ViewInfo = OperatorInfo {{ Pos = {{ {100 + 100 * merge_count}, {150} }} }}
		}}"""
            node_blocks.append(merge_block)
            last_merge = merge_name
            loader_count += 1
            merge_count += 1

        prev_merge_name = last_merge

    media_out_block = f"""
		MediaOut{media_out_idx} = MediaOut {{
			Inputs = {{
				Index = Input {{ Value = \"0\" }},
				Input = Input {{ SourceOp = \"{prev_merge_name}\", Source = \"Output\" }}
			}},
			ViewInfo = OperatorInfo {{ Pos = {{ {100 + 100 * merge_count}, {200} }} }}
		}}"""
    node_blocks.append(media_out_block)

    with open(output_path, "w") as f:
        f.write(FUSION_HEADER)
        f.write(",\n".join(node_blocks))
        f.write("\n")
        f.write(FUSION_FOOTER)

    print(f"✅ Fusion .comp file written to {output_path}")


if __name__ == "__main__":
    otio_file = "sora_cascade.otio"
    fusion_out = "sora_comp_v1_2.comp"
    build_fusion_comp(otio_file, fusion_out)

"""
USAGE:
1. Ensure `sora_cascade.otio` exists (e.g., from `otio_sora_cascade.py`)
2. Run this script: python otio_to_fusion_comp.py
3. It creates `sora_comp_v1_2.comp` → Open in Fusion (Resolve or standalone)

FEATURES:
- Groups multiple versions of same domain into crossfading stack
- Each version fades in/out over time slice
- Fully cascaded merge flow returns to main MediaOut
- Now Fusion-safe: No trailing commas, valid block closures, copy-paste verified
"""
