"""Command-line interface for the cyber antiquing generator."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .generator import describe_steps, generate_antiqued_image
from .presets import available_presets
from .strength import available_strength_presets, get_strength_preset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cyber-antiquing",
        description="Simulate repeated repost compression and watermarking across social platforms.",
    )
    parser.add_argument("input", nargs="?", type=Path, help="Input image path.")
    parser.add_argument("output", nargs="?", type=Path, help="Output image path.")
    parser.add_argument(
        "--strength",
        choices=tuple(sorted(available_strength_presets())),
        default="classic",
        help="Named strength preset. Default: classic.",
    )
    parser.add_argument("-n", "--passes", type=int, help="Override repost/upload pass count from the strength preset.")
    parser.add_argument(
        "-p",
        "--platform",
        action="append",
        dest="platforms",
        help="Platform preset to use. Can be repeated. Default: tieba, weibo, qq, wechat.",
    )
    parser.add_argument(
        "--random-platforms",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Randomly choose the platform for each pass. Default: true.",
    )
    parser.add_argument(
        "--random-methods",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Randomly sample compression and watermark parameters within each preset. Default: true.",
    )
    parser.add_argument("--seed", type=int, help="Random seed for reproducible output.")
    parser.add_argument(
        "--intensity",
        type=float,
        help="Override artifact intensity from the strength preset. Useful range: 0.5-2.0.",
    )
    parser.add_argument("--no-watermark", action="store_true", help="Disable layered platform watermarks.")
    parser.add_argument(
        "--keep-size",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Resize the final image back to the original dimensions. Default: true.",
    )
    parser.add_argument("--final-quality", type=int, default=88, help="Final JPEG/WEBP save quality, 1-95.")
    parser.add_argument("--final-format", choices=("JPEG", "JPG", "PNG", "WEBP"), help="Override output format.")
    parser.add_argument("--list-platforms", action="store_true", help="List platform presets and exit.")
    parser.add_argument("--list-strengths", action="store_true", help="List strength presets and exit.")
    parser.add_argument("--quiet", action="store_true", help="Do not print the pass chain.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_platforms:
        _print_platforms()
        return 0

    if args.list_strengths:
        _print_strengths()
        return 0

    if args.input is None or args.output is None:
        parser.error("input and output are required unless --list-platforms is used")

    try:
        strength = get_strength_preset(args.strength)
        config = strength.to_config(
            passes=args.passes,
            platforms=tuple(args.platforms) if args.platforms else None,
            random_platforms=args.random_platforms,
            random_methods=args.random_methods,
            seed=args.seed,
            intensity=args.intensity,
            add_watermarks=not args.no_watermark,
            preserve_size=args.keep_size,
            final_quality=args.final_quality,
            final_format=args.final_format,
        )
        result = generate_antiqued_image(args.input, args.output, config)
    except Exception as exc:  # pragma: no cover - CLI boundary
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not args.quiet:
        print(f"saved: {result.output_path}")
        print(describe_steps(result.steps))
    return 0


def _print_platforms() -> None:
    for key, preset in sorted(available_presets().items()):
        formats = ", ".join(preset.formats)
        print(f"{key:<8} {preset.display_name:<12} codecs={formats:<10} watermark={preset.watermark}")


def _print_strengths() -> None:
    for key, preset in sorted(available_strength_presets().items()):
        platforms = " -> ".join(preset.platforms)
        print(f"{key:<10} passes={preset.passes:<2} intensity={preset.intensity:<4} platforms={platforms}")
