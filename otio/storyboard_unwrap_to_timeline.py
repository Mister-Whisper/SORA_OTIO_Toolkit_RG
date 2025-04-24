# storyboard_unwrap_to_timeline.py
# Description: Unwraps Sora storyboard outputs into a timeline that reflects true clip timings
# Uses Resolve-style logic: places, ripples, and stacks storyboard steps based on start_time and duration

import opentimelineio as otio
from opentimelineio.opentime import RationalTime, TimeRange
import os, json

FRAME_RATE = 24

class StoryboardTimelineBuilder:
    def __init__(self, json_path):
        self.json_path = json_path
        self.tracks = []
        self.timeline = otio.schema.Timeline(name="Sora Storyboard Unwrapped")
        self.occupied = []  # track-level clip occupancy

    def _is_slot_free(self, start, end, track_idx):
        for s, e in self.occupied[track_idx]:
            if start < e and end > s:
                return False
        return True

    def _find_available_track(self, start, end):
        for i, occ in enumerate(self.occupied):
            if self._is_slot_free(start, end, i):
                return i
        self.occupied.append([])
        return len(self.occupied) - 1

    def _rational(self, seconds):
        return RationalTime(seconds, FRAME_RATE)

    def _insert_clip(self, track_idx, name, start, duration, url=None):
        src_range = TimeRange(self._rational(0), self._rational(duration))
        clip = otio.schema.Clip(
            name=name,
            source_range=src_range,
            media_reference=otio.schema.ExternalReference(target_url=url or "")
        )
        if len(self.tracks) <= track_idx:
            self.tracks.append(otio.schema.Track(name=f"V{track_idx+1}", kind=otio.schema.TrackKind.Video))
        track = self.tracks[track_idx]

        current_time = track.duration().value
        if start > current_time:
            track.append(otio.schema.Gap(self._rational(start - current_time)))

        assert self._is_slot_free(start, start + duration, track_idx), f"❌ Overlap in track {track_idx} at {start}s"

        track.append(clip)
        self.occupied[track_idx].append((start, start + duration))

    def build(self):
        with open(self.json_path, "r") as f:
            data = json.load(f)

        gen_id = data.get("generation_id", "storyboard")
        for i, clip in enumerate(data.get("clips", [])):
            name = f"clip_{i+1}_{clip.get('media_type')}"
            start = clip.get("start_time", 0)
            duration = clip.get("duration", 0.1)  # force small viewable clip if zero
            media_url = clip.get("source_media_url") or f"file://{clip.get('source_media_uuid', name)}.mp4"
            track_idx = self._find_available_track(start, start + duration)
            self._insert_clip(track_idx, name, start, duration, media_url)

        for t in self.tracks:
            self.timeline.tracks.append(t)
        return self.timeline

if __name__ == "__main__":
    builder = StoryboardTimelineBuilder("./storyboard_gen.json")
    result = builder.build()
    otio.adapters.write_to_file(result, "storyboard_unwrapped.otio")
    print("✅ Unwrapped storyboard written to storyboard_unwrapped.otio")

"""
USAGE:
1. Place a single storyboard .json (from Sora extractor) as ./storyboard_gen.json
2. Run: python storyboard_unwrap_to_timeline.py
3. Output: storyboard_unwrapped.otio
   → Can be opened in Resolve for timeline-aligned view of prompts/media

- Supports ripple, track stacking, gaps
- Prompts with no media will still be visualized (0.1s dummy duration)
- Automatically stacks overlapping items into V2, V3...
"""
