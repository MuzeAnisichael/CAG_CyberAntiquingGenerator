"""Gradio Web UI for the cyber antiquing generator."""

from __future__ import annotations

from pathlib import Path
import tempfile

from PIL import Image, ImageDraw

from .generator import describe_steps, generate_antiqued_pil
from .presets import available_presets
from .strength import available_strength_presets, get_strength_preset


DEFAULT_STRENGTH = "classic"


def build_app():
    try:
        import gradio as gr
    except ImportError as exc:  # pragma: no cover - optional dependency boundary
        raise RuntimeError("Gradio is not installed. Run `pip install -r requirements.txt`.") from exc

    platform_keys = tuple(sorted(available_presets()))
    strength_keys = tuple(available_strength_presets())

    with gr.Blocks(title="CAG Cyber Antiquing Generator") as app:
        gr.Markdown("# CAG Cyber Antiquing Generator")

        with gr.Row():
            input_image = gr.Image(label="原图", type="pil", height=420)
            output_image = gr.Image(label="包浆结果", type="pil", height=420)

        with gr.Row():
            run_button = gr.Button("生成包浆", variant="primary")
            sample_button = gr.Button("使用示例图")
            clear_button = gr.ClearButton([input_image, output_image])

        with gr.Row():
            strength = gr.Dropdown(
                choices=strength_keys,
                value=DEFAULT_STRENGTH,
                label="强度预设",
            )
            passes = gr.Slider(1, 30, value=5, step=1, label="包浆次数")
            intensity = gr.Slider(0.3, 2.5, value=1.0, step=0.05, label="强度倍率")
            seed = gr.Number(value=42, precision=0, label="随机种子")

        with gr.Row():
            platforms = gr.CheckboxGroup(
                choices=platform_keys,
                value=["tieba", "weibo", "qq", "wechat"],
                label="平台链路",
            )
            with gr.Column():
                random_platforms = gr.Checkbox(value=True, label="随机平台")
                random_methods = gr.Checkbox(value=True, label="随机方法")
                add_watermarks = gr.Checkbox(value=True, label="叠加水印")
                keep_size = gr.Checkbox(value=True, label="保持原尺寸")

        summary = gr.Textbox(label="处理链路", lines=9)

        strength.change(
            fn=_strength_defaults,
            inputs=strength,
            outputs=[passes, intensity, platforms, random_platforms, random_methods, add_watermarks, keep_size],
        )
        sample_button.click(fn=create_sample_image, outputs=input_image)
        run_button.click(
            fn=process_image,
            inputs=[
                input_image,
                strength,
                passes,
                intensity,
                platforms,
                random_platforms,
                random_methods,
                add_watermarks,
                keep_size,
                seed,
            ],
            outputs=[output_image, summary],
        )

    return app


def process_image(
    image: Image.Image | None,
    strength_key: str,
    passes: int,
    intensity: float,
    platforms: list[str],
    random_platforms: bool,
    random_methods: bool,
    add_watermarks: bool,
    keep_size: bool,
    seed: int | float | None,
) -> tuple[Image.Image, str]:
    if image is None:
        raise ValueError("please upload an image or use the sample image")
    if not platforms:
        platforms = list(get_strength_preset(strength_key).platforms)

    seed_value = None if seed is None else int(seed)
    preset = get_strength_preset(strength_key)
    config = preset.to_config(
        passes=int(passes),
        intensity=float(intensity),
        platforms=tuple(platforms),
        random_platforms=bool(random_platforms),
        random_methods=bool(random_methods),
        add_watermarks=bool(add_watermarks),
        preserve_size=bool(keep_size),
        seed=seed_value,
    )
    result = generate_antiqued_pil(image, config)
    summary = _summary(config.passes, config.intensity, describe_steps(result.steps))
    return result.image, summary


def create_sample_image() -> Image.Image:
    image = Image.new("RGB", (720, 480), (240, 238, 232))
    draw = ImageDraw.Draw(image)
    draw.rectangle((56, 52, 470, 244), fill=(222, 46, 68))
    draw.ellipse((320, 150, 650, 408), fill=(48, 96, 210))
    draw.rectangle((92, 292, 400, 374), fill=(34, 34, 34))
    draw.text((116, 318), "CYBER ANTIQUING", fill=(255, 255, 255))
    draw.text((58, 420), "sample source image", fill=(30, 30, 30))
    return image


def _strength_defaults(strength_key: str):
    preset = get_strength_preset(strength_key)
    return (
        preset.passes,
        preset.intensity,
        list(preset.platforms),
        preset.random_platforms,
        preset.random_methods,
        preset.add_watermarks,
        preset.preserve_size,
    )


def _summary(passes: int, intensity: float, steps: str) -> str:
    return f"passes={passes}, intensity={intensity:.2f}\n\n{steps}"


def main() -> None:
    app = build_app()
    app.launch()


def export_demo_image(path: str | Path | None = None) -> Path:
    output = Path(path) if path else Path(tempfile.gettempdir()) / "cag_sample_source.png"
    create_sample_image().save(output)
    return output


if __name__ == "__main__":
    main()
