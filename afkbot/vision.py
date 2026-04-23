from pathlib import Path

import cv2
import mss
import numpy as np

from afkbot.models import Region


def load_template(template_path: Path) -> np.ndarray:
    template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
    if template is None:
        raise FileNotFoundError(f"讀不到模板圖片: {template_path}")
    return template


def grab_gray_frame(sct: mss.mss, region: Region) -> np.ndarray:
    frame = np.array(sct.grab(region))
    bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)


def match_template(
    frame_gray: np.ndarray,
    template_gray: np.ndarray,
    match_mode: str,
    pixel_tolerance: int,
) -> float:
    if match_mode == "exact_frame":
        if frame_gray.shape != template_gray.shape:
            return 0.0
        difference = cv2.absdiff(frame_gray, template_gray)
        matched_pixels = difference <= pixel_tolerance
        return float(np.count_nonzero(matched_pixels) / matched_pixels.size)

    result = cv2.matchTemplate(frame_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    return float(max_val)


def resolve_capture_region(
    sct: mss.mss, configured_region: Region | None
) -> Region:
    if configured_region:
        return {
            "left": int(configured_region["left"]),
            "top": int(configured_region["top"]),
            "width": int(configured_region["width"]),
            "height": int(configured_region["height"]),
        }

    monitor = sct.monitors[1]
    return {
        "left": int(monitor["left"]),
        "top": int(monitor["top"]),
        "width": int(monitor["width"]),
        "height": int(monitor["height"]),
    }


def to_absolute_region(base_region: Region, scene_region: Region | None) -> Region:
    if not scene_region:
        return dict(base_region)

    return {
        "left": int(base_region["left"]) + int(scene_region["left"]),
        "top": int(base_region["top"]) + int(scene_region["top"]),
        "width": int(scene_region["width"]),
        "height": int(scene_region["height"]),
    }
