"""Core image processing pipeline for cyber antiquing.

The visual damage is built mostly from real lossy round-trips: resizing,
JPEG/WebP encoding, JPEG 4:2:0 chroma subsampling, and palette quantization.
Small synthetic perturbations model differences between platform processing
pipelines and make repeated repost chains less uniform.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import io
import math
import random
from typing import Iterable

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

from .presets import PlatformPreset, get_preset


DEFAULT_PLATFORMS = ("tieba", "weibo", "qq", "wechat")
SUPPORTED_SAVE_FORMATS = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
}


@dataclass(frozen=True)
class AntiquingConfig:
    passes: int = 5
    platforms: tuple[str, ...] = DEFAULT_PLATFORMS
    random_platforms: bool = True
    random_methods: bool = True
    seed: int | None = None
    intensity: float = 1.0
    add_watermarks: bool = True
    preserve_size: bool = True
    final_quality: int = 88
    final_format: str | None = None


@dataclass(frozen=True)
class AntiquingStep:
    index: int
    platform: str
    codec: str
    quality: int
    max_edge: int
    scale: float
    watermark: str | None


@dataclass(frozen=True)
class AntiquingResult:
    output_path: Path
    steps: tuple[AntiquingStep, ...]


@dataclass(frozen=True)
class AntiquingImageResult:
    image: Image.Image
    steps: tuple[AntiquingStep, ...]


def generate_antiqued_image(
    input_path: str | Path,
    output_path: str | Path,
    config: AntiquingConfig | None = None,
) -> AntiquingResult:
    """Generate an antiqued image and return the platform chain that was used."""

    input_path = Path(input_path)
    output_path = Path(output_path)

    with Image.open(input_path) as source:
        result = generate_antiqued_pil(source, config)

    _save_final(result.image, output_path, config or AntiquingConfig())
    return AntiquingResult(output_path=output_path, steps=result.steps)


def generate_antiqued_pil(
    image: Image.Image,
    config: AntiquingConfig | None = None,
) -> AntiquingImageResult:
    """Generate an antiqued image from an in-memory Pillow image."""

    config = config or AntiquingConfig()
    _validate_config(config)

    rng = random.Random(config.seed)
    presets = tuple(get_preset(key) for key in config.platforms)
    image = _normalize_input(image)

    original_size = image.size
    steps: list[AntiquingStep] = []

    for index in range(1, config.passes + 1):
        preset = _choose_preset(presets, index, rng, config.random_platforms)
        image, step = _apply_platform_pass(image, preset, index, rng, config)
        steps.append(step)

    if config.preserve_size and image.size != original_size:
        image = image.resize(original_size, Image.Resampling.BICUBIC)

    return AntiquingImageResult(image=image, steps=tuple(steps))


def _validate_config(config: AntiquingConfig) -> None:
    if config.passes < 1:
        raise ValueError("passes must be at least 1")
    if not config.platforms:
        raise ValueError("at least one platform preset is required")


def _apply_platform_pass(
    image: Image.Image,
    preset: PlatformPreset,
    index: int,
    rng: random.Random,
    config: AntiquingConfig,
) -> tuple[Image.Image, AntiquingStep]:
    intensity = _clamp(config.intensity, 0.1, 3.0)
    codec = _sample_choice(preset.formats, rng, config.random_methods)
    quality = _scaled_quality(_sample_int(preset.jpeg_quality, rng, config.random_methods), intensity)
    max_edge = _scaled_max_edge(_sample_int(preset.max_edge, rng, config.random_methods), intensity)
    scale = _scaled_scale(_sample_float(preset.scale, rng, config.random_methods), intensity)

    image = _platform_resize(image, max_edge)
    image = _repost_resample(image, scale)

    if config.add_watermarks:
        watermark = _watermark_text(preset, index, rng, config.random_methods)
        opacity = _sample_int(preset.watermark_opacity, rng, config.random_methods)
        image = _draw_watermark(image, watermark, opacity, rng, config.random_methods)
    else:
        watermark = None

    image = _roundtrip_compress(image, codec, quality, preset, rng, config.random_methods)
    image = _apply_platform_tuning(image, preset, rng, config.random_methods, intensity)

    return image, AntiquingStep(
        index=index,
        platform=preset.key,
        codec=codec,
        quality=quality,
        max_edge=max_edge,
        scale=scale,
        watermark=watermark,
    )


def _normalize_input(image: Image.Image) -> Image.Image:
    image = image.copy()
    image = _apply_exif_orientation(image)
    if image.mode == "RGB":
        return image
    if image.mode in {"RGBA", "LA"}:
        background = Image.new("RGB", image.size, (255, 255, 255))
        alpha = image.getchannel("A")
        background.paste(image.convert("RGB"), mask=alpha)
        return background
    return image.convert("RGB")


def _apply_exif_orientation(image: Image.Image) -> Image.Image:
    try:
        return ImageOps.exif_transpose(image)
    except Exception:
        return image


def _choose_preset(
    presets: tuple[PlatformPreset, ...],
    index: int,
    rng: random.Random,
    random_platforms: bool,
) -> PlatformPreset:
    if random_platforms:
        return rng.choice(presets)
    return presets[(index - 1) % len(presets)]


def _platform_resize(image: Image.Image, max_edge: int) -> Image.Image:
    width, height = image.size
    longest = max(width, height)
    if longest <= max_edge:
        return image
    ratio = max_edge / longest
    target = (max(1, round(width * ratio)), max(1, round(height * ratio)))
    return image.resize(target, Image.Resampling.LANCZOS)


def _repost_resample(image: Image.Image, scale: float) -> Image.Image:
    if scale >= 0.995:
        return image
    width, height = image.size
    downsampled = (
        max(1, round(width * scale)),
        max(1, round(height * scale)),
    )
    return image.resize(downsampled, Image.Resampling.BICUBIC)


def _draw_watermark(
    image: Image.Image,
    text: str,
    opacity: int,
    rng: random.Random,
    random_methods: bool,
) -> Image.Image:
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    width, height = image.size
    margin = _sample_int((8, 22), rng, random_methods)

    positions = (
        (margin, margin),
        (width - text_width - margin, margin),
        (margin, height - text_height - margin),
        (width - text_width - margin, height - text_height - margin),
        (
            _sample_int((margin, max(margin, width - text_width - margin)), rng, random_methods),
            _sample_int((margin, max(margin, height - text_height - margin)), rng, random_methods),
        ),
    )
    x, y = rng.choice(positions) if random_methods else positions[3]
    x = max(margin, min(x, max(margin, width - text_width - margin)))
    y = max(margin, min(y, max(margin, height - text_height - margin)))

    shadow_opacity = max(20, opacity // 2)
    draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0, shadow_opacity))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, opacity))
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def _roundtrip_compress(
    image: Image.Image,
    codec: str,
    quality: int,
    preset: PlatformPreset,
    rng: random.Random,
    random_methods: bool,
) -> Image.Image:
    buffer = io.BytesIO()
    codec = codec.upper()

    try:
        if codec == "PNG8":
            colors = _sample_int(preset.palette_colors, rng, random_methods)
            quantized = image.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
            quantized.save(buffer, format="PNG", optimize=True)
        elif codec == "WEBP":
            image.save(buffer, format="WEBP", quality=quality, method=4)
        else:
            image.save(
                buffer,
                format="JPEG",
                quality=quality,
                subsampling=2,
                optimize=True,
                progressive=random_methods and rng.random() < 0.35,
            )
    except OSError:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=quality, subsampling=2)

    buffer.seek(0)
    with Image.open(buffer) as compressed:
        return compressed.convert("RGB").copy()


def _apply_platform_tuning(
    image: Image.Image,
    preset: PlatformPreset,
    rng: random.Random,
    random_methods: bool,
    intensity: float,
) -> Image.Image:
    contrast = _scaled_factor(_sample_float(preset.contrast, rng, random_methods), intensity)
    sharpness = _scaled_factor(_sample_float(preset.sharpness, rng, random_methods), intensity)
    blur = _sample_float(preset.blur, rng, random_methods) * intensity
    noise = _sample_float(preset.noise, rng, random_methods) * intensity
    color_shift = _scaled_integer(_sample_int(preset.color_shift, rng, random_methods), intensity, 0, 48)

    image = ImageEnhance.Contrast(image).enhance(contrast)
    image = ImageEnhance.Sharpness(image).enhance(sharpness)
    if blur > 0.03:
        image = image.filter(ImageFilter.GaussianBlur(radius=blur))
    if color_shift:
        image = _shift_color(image, color_shift, rng, random_methods)
    if noise > 0.05:
        image = _add_luma_noise(image, noise)
    return image


def _shift_color(image: Image.Image, max_shift: int, rng: random.Random, random_methods: bool) -> Image.Image:
    channels = []
    offsets = (
        _sample_int((-max_shift, max_shift), rng, random_methods),
        _sample_int((-max_shift, max_shift), rng, random_methods),
        _sample_int((-max_shift, max_shift), rng, random_methods),
    )
    for channel, offset in zip(image.split(), offsets):
        channels.append(channel.point(lambda value, delta=offset: _int_clamp(value + delta)))
    return Image.merge("RGB", channels)


def _add_luma_noise(image: Image.Image, strength: float) -> Image.Image:
    noise = Image.effect_noise(image.size, strength * 3.0).convert("L")
    noise_rgb = Image.merge("RGB", (noise, noise, noise))
    return ImageChops.add(image, noise_rgb, scale=1.0, offset=-128)


def _watermark_text(preset: PlatformPreset, index: int, rng: random.Random, random_methods: bool) -> str:
    if not random_methods:
        return f"{preset.watermark}_{index:02d}"
    suffix = rng.choice(("", "", f"_{index:02d}", "_repost", "_compressed"))
    return f"{preset.watermark}{suffix}"


def _save_final(image: Image.Image, output_path: Path, config: AntiquingConfig) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fmt = _resolve_output_format(output_path, config.final_format)
    quality = _int_clamp(config.final_quality, 1, 95)
    if fmt == "JPEG":
        image.save(output_path, format=fmt, quality=quality, subsampling=2, optimize=True)
    elif fmt == "WEBP":
        image.save(output_path, format=fmt, quality=quality, method=4)
    else:
        image.save(output_path, format=fmt, optimize=True)


def _resolve_output_format(output_path: Path, requested: str | None) -> str:
    if requested:
        fmt = requested.upper()
        if fmt == "JPG":
            return "JPEG"
        if fmt in {"JPEG", "PNG", "WEBP"}:
            return fmt
        raise ValueError("final_format must be JPEG, PNG, or WEBP")
    return SUPPORTED_SAVE_FORMATS.get(output_path.suffix.lower(), "JPEG")


def _sample_choice(values: tuple[str, ...], rng: random.Random, random_methods: bool) -> str:
    return rng.choice(values) if random_methods else values[0]


def _sample_int(bounds: tuple[int, int], rng: random.Random, random_methods: bool) -> int:
    low, high = bounds
    if low > high:
        low, high = high, low
    return rng.randint(low, high) if random_methods else round((low + high) / 2)


def _sample_float(bounds: tuple[float, float], rng: random.Random, random_methods: bool) -> float:
    low, high = bounds
    if low > high:
        low, high = high, low
    return rng.uniform(low, high) if random_methods else (low + high) / 2.0


def _scaled_quality(value: int, intensity: float) -> int:
    return _int_clamp(round(value / intensity), 4, 95)


def _scaled_max_edge(value: int, intensity: float) -> int:
    return max(160, round(value / math.sqrt(intensity)))


def _scaled_scale(value: float, intensity: float) -> float:
    return _clamp(1.0 - ((1.0 - value) * intensity), 0.18, 1.0)


def _scaled_factor(value: float, intensity: float) -> float:
    return _clamp(1.0 + ((value - 1.0) * intensity), 0.25, 2.5)


def _scaled_integer(value: int, intensity: float, minimum: int, maximum: int) -> int:
    return _int_clamp(round(value * intensity), minimum, maximum)


def _int_clamp(value: int | float, minimum: int = 0, maximum: int = 255) -> int:
    return int(max(minimum, min(maximum, round(value))))


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def describe_steps(steps: Iterable[AntiquingStep]) -> str:
    lines = []
    for step in steps:
        watermark = step.watermark or "none"
        lines.append(
            f"{step.index:02d}. {step.platform:<7} {step.codec:<5} "
            f"q={step.quality:<2} max_edge={step.max_edge:<4} "
            f"scale={step.scale:.2f} watermark={watermark}"
        )
    return "\n".join(lines)
