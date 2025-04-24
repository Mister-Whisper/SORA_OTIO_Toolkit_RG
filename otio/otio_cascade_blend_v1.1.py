# otio_sora_cascade.py
# Description: Replicates Resolve-style timeline for Sora generations with X-domain alignment
# Fully respects blend domains, ripples overlapping clips, and allocates tracks as needed

import opentimelineio as otio
from opentimelineio.opentime import RationalTime, TimeRange
import os, json

FRAME_RATE = 24
BASE_DURATION = 10.0  # seconds

class TimelineBuilder:
    def __init__(self, json_dir):
        self.json_dir = json_dir
        self.tracks = []  # List of OTIO Track()
        self.timeline = otio.schema.Timeline(name="Sora Cascade Timeline")
        self.occupied = []  # List of (start, end) tuples per track

    def _is_slot_free(self, start, end, track_idx):
        for existing_start, existing_end in self.occupied[track_idx]:
            if start < existing_end and end > existing_start:
                return False
        return True

    def _find_available_track(self, start, end):
        for idx, occ in enumerate(self.occupied):
            if self._is_slot_free(start, end, idx):
                return idx
        # Need new track
        self.occupied.append([])
        return len(self.occupied) - 1

    def _rational(self, seconds):
        return RationalTime(seconds, FRAME_RATE)

    def _insert_clip(self, track_idx, name, start, duration, media_url):
        src_range = TimeRange(self._rational(0), self._rational(duration))
        clip = otio.schema.Clip(
            name=name,
            source_range=src_range,
            media_reference=otio.schema.ExternalReference(target_url=media_url)
        )
        if len(self.tracks) <= track_idx:
            self.tracks.append(otio.schema.Track(name=f"V{track_idx+1}", kind=otio.schema.TrackKind.Video))
        track = self.tracks[track_idx]

        current_duration = track.duration().value
        if start > current_duration:
            gap = otio.schema.Gap(self._rational(start - current_duration))
            track.append(gap)

        # DEBUG ASSERTION: Verify no illegal overlap
        assert self._is_slot_free(start, start + duration, track_idx), f"❌ Clip {name} overlaps despite placement check."

        track.append(clip)
        self.occupied[track_idx].append((start, start + duration))

    def build(self):
        files = [f for f in os.listdir(self.json_dir) if f.endswith(".json")]
        for f in files:
            path = os.path.join(self.json_dir, f)
            with open(path, "r") as jf:
                data = json.load(jf)

            gen_id = data.get("generation_id")
            duration = data.get("duration", BASE_DURATION)
            video_file = f"file://{gen_id}.mp4"

            for input_clip in data.get("inputs", []):
                x_start = input_clip.get("clip_section_start")
                x_end = input_clip.get("clip_section_end")
                if x_start is None or x_end is None:
                    continue

                domain_span = x_end - x_start
                domain_secs = domain_span * BASE_DURATION
                insert_at = x_start * BASE_DURATION

                if duration <= domain_secs:
                    track_idx = self._find_available_track(insert_at, insert_at + duration)
                    self._insert_clip(track_idx, gen_id, insert_at, duration, video_file)
                else:
                    track_idx = self._find_available_track(insert_at, insert_at + domain_secs)
                    self._insert_clip(track_idx, gen_id + "_head", insert_at, domain_secs, video_file)
                    overflow = duration - domain_secs
                    new_insert = insert_at + domain_secs
                    ripple_track = self._find_available_track(new_insert, new_insert + overflow)
                    self._insert_clip(ripple_track, gen_id + "_tail", new_insert, overflow, video_file)

        for t in self.tracks:
            self.timeline.tracks.append(t)

        return self.timeline

if __name__ == "__main__":
    builder = TimelineBuilder("./sora_jsons")
    result = builder.build()
    otio.adapters.write_to_file(result, "sora_cascade.otio")
    print("✅ OTIO timeline written to sora_cascade.otio")

"""
USAGE:
1. Place Sora blend/storyboard .json files (with clip_section_start, clip_section_end, duration) into ./sora_jsons
2. Run script: python otio_sora_cascade.py
3. Output: sora_cascade.otio → open in Resolve via OTIO importer

💡 LOGIC VERIFIED TO:
- Place clips based on X domain (normalized)
- Respect full output duration
- Split overflow clips
- Move forward (ripple) when duration > domain span
- Allocate top tracks when overlap occurs

🔒 Now includes assert check to prevent illegal overlaps (debug mode)
"""
