"""Platform presets for repeated social-platform image degradation."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class PlatformPreset:
    key: str
    display_name: str
    watermark: str
    formats: tuple[str, ...]
    jpeg_quality: tuple[int, int]
    max_edge: tuple[int, int]
    scale: tuple[float, float]
    noise: tuple[float, float]
    color_shift: tuple[int, int]
    blur: tuple[float, float]
    sharpness: tuple[float, float]
    contrast: tuple[float, float]
    watermark_opacity: tuple[int, int] = (44, 112)
    palette_colors: tuple[int, int] = (48, 160)


_PRESETS = {
    "tieba": PlatformPreset(
        key="tieba",
        display_name="Baidu Tieba",
        watermark="baidutieba",
        formats=("JPEG",),
        jpeg_quality=(12, 34),
        max_edge=(720, 1280),
        scale=(0.70, 0.96),
        noise=(0.8, 4.5),
        color_shift=(2, 16),
        blur=(0.0, 0.40),
        sharpness=(0.72, 1.18),
        contrast=(0.82, 1.10),
        palette_colors=(32, 96),
    ),
    "weibo": PlatformPreset(
        key="weibo",
        display_name="Weibo",
        watermark="weibo",
        formats=("JPEG", "WEBP"),
        jpeg_quality=(30, 62),
        max_edge=(1080, 2048),
        scale=(0.78, 1.00),
        noise=(0.3, 2.8),
        color_shift=(0, 10),
        blur=(0.0, 0.26),
        sharpness=(0.88, 1.36),
        contrast=(0.90, 1.18),
    ),
    "qq": PlatformPreset(
        key="qq",
        display_name="QQ",
        watermark="QQ",
        formats=("JPEG", "PNG8"),
        jpeg_quality=(20, 52),
        max_edge=(640, 1440),
        scale=(0.64, 0.94),
        noise=(0.6, 4.2),
        color_shift=(2, 12),
        blur=(0.0, 0.46),
        sharpness=(0.72, 1.48),
        contrast=(0.84, 1.20),
        palette_colors=(32, 128),
    ),
    "wechat": PlatformPreset(
        key="wechat",
        display_name="WeChat",
        watermark="WeChat",
        formats=("JPEG",),
        jpeg_quality=(38, 74),
        max_edge=(1080, 1920),
        scale=(0.82, 1.00),
        noise=(0.1, 1.9),
        color_shift=(0, 7),
        blur=(0.0, 0.22),
        sharpness=(0.84, 1.18),
        contrast=(0.92, 1.08),
    ),
    "douyin": PlatformPreset(
        key="douyin",
        display_name="Douyin",
        watermark="douyin",
        formats=("JPEG", "WEBP"),
        jpeg_quality=(24, 56),
        max_edge=(720, 1920),
        scale=(0.72, 0.98),
        noise=(0.4, 3.4),
        color_shift=(2, 16),
        blur=(0.0, 0.32),
        sharpness=(0.92, 1.65),
        contrast=(0.95, 1.28),
    ),
    "rednote": PlatformPreset(
        key="rednote",
        display_name="RedNote",
        watermark="rednote",
        formats=("JPEG", "WEBP"),
        jpeg_quality=(34, 68),
        max_edge=(1080, 2048),
        scale=(0.78, 1.00),
        noise=(0.2, 2.4),
        color_shift=(0, 9),
        blur=(0.0, 0.20),
        sharpness=(0.88, 1.34),
        contrast=(0.92, 1.16),
    ),
}

PRESETS = MappingProxyType(_PRESETS)


def available_presets() -> dict[str, PlatformPreset]:
    return dict(PRESETS)


def get_preset(key: str) -> PlatformPreset:
    try:
        return PRESETS[key.lower()]
    except KeyError as exc:
        choices = ", ".join(sorted(PRESETS))
        raise ValueError(f"unknown platform preset {key!r}; choose from: {choices}") from exc
