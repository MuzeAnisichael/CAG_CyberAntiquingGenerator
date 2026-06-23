"""CLI and compatibility entry point for the Cyber Antiquing Generator."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Union


sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from cyber_antiquing import AntiquingConfig, generate_antiqued_image  # noqa: E402
from cyber_antiquing.cli import main  # noqa: E402


PathLike = Union[str, Path]


def generate_distorted_image(
    input_path: PathLike,
    output_path: PathLike,
    pixelation_factor: int | bool = 5,
    noise_factor: float | bool = 0.01,
    color_shift_factor: float | bool = 0.5,
    compression_quality: int = 10,
    repeat_compression_times: int = 5,
    format_conversion: str = "JPEG",
    add_watermark: str | bool = "baidutieba",
):
    """Legacy API wrapper around the new platform-chain generator."""

    del format_conversion

    intensity = 1.0
    if compression_quality < 35:
        intensity += min((35 - compression_quality) / 50.0, 0.45)
    if pixelation_factor:
        intensity += min(max(int(pixelation_factor), 1) / 24.0, 0.35)
    if noise_factor:
        intensity += min(float(noise_factor) * 10.0, 0.25)
    if color_shift_factor:
        intensity += min(float(color_shift_factor) / 2.0, 0.25)

    config = AntiquingConfig(
        passes=max(1, int(repeat_compression_times)),
        random_platforms=True,
        random_methods=True,
        intensity=min(intensity, 2.2),
        add_watermarks=bool(add_watermark),
    )
    return generate_antiqued_image(input_path, output_path, config)


if __name__ == "__main__":
    raise SystemExit(main())
