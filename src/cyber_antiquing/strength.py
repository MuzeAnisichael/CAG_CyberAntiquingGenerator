"""Named strength presets for common cyber antiquing styles."""

from __future__ import annotations

from dataclasses import dataclass

from .generator import AntiquingConfig


@dataclass(frozen=True)
class StrengthPreset:
    key: str
    label: str
    description: str
    passes: int
    intensity: float
    platforms: tuple[str, ...]
    random_platforms: bool = True
    random_methods: bool = True
    add_watermarks: bool = True
    preserve_size: bool = True

    def to_config(
        self,
        *,
        passes: int | None = None,
        intensity: float | None = None,
        platforms: tuple[str, ...] | None = None,
        random_platforms: bool | None = None,
        random_methods: bool | None = None,
        add_watermarks: bool | None = None,
        preserve_size: bool | None = None,
        seed: int | None = None,
        final_quality: int = 88,
        final_format: str | None = None,
    ) -> AntiquingConfig:
        return AntiquingConfig(
            passes=passes if passes is not None else self.passes,
            platforms=platforms if platforms else self.platforms,
            random_platforms=self.random_platforms if random_platforms is None else random_platforms,
            random_methods=self.random_methods if random_methods is None else random_methods,
            seed=seed,
            intensity=intensity if intensity is not None else self.intensity,
            add_watermarks=self.add_watermarks if add_watermarks is None else add_watermarks,
            preserve_size=self.preserve_size if preserve_size is None else preserve_size,
            final_quality=final_quality,
            final_format=final_format,
        )


STRENGTH_PRESETS = {
    "light": StrengthPreset(
        key="light",
        label="Light",
        description="A few reposts with visible but restrained compression.",
        passes=3,
        intensity=0.75,
        platforms=("wechat", "weibo"),
    ),
    "classic": StrengthPreset(
        key="classic",
        label="Classic",
        description="Balanced social-platform repost artifacts.",
        passes=5,
        intensity=1.0,
        platforms=("tieba", "weibo", "qq", "wechat"),
    ),
    "heavy": StrengthPreset(
        key="heavy",
        label="Heavy",
        description="Obvious compression, resampling, and layered marks.",
        passes=9,
        intensity=1.35,
        platforms=("tieba", "qq", "wechat", "weibo", "douyin"),
    ),
    "ancestral": StrengthPreset(
        key="ancestral",
        label="Ancestral",
        description="Old repost chain with low-quality forum and chat app damage.",
        passes=14,
        intensity=1.65,
        platforms=("tieba", "qq", "tieba", "wechat", "weibo"),
    ),
    "abyss": StrengthPreset(
        key="abyss",
        label="Abyss",
        description="Maximum meme corrosion for intentionally cursed outputs.",
        passes=20,
        intensity=2.15,
        platforms=("tieba", "qq", "douyin", "weibo", "rednote", "wechat"),
    ),
}


def available_strength_presets() -> dict[str, StrengthPreset]:
    return dict(STRENGTH_PRESETS)


def get_strength_preset(key: str) -> StrengthPreset:
    try:
        return STRENGTH_PRESETS[key.lower()]
    except KeyError as exc:
        choices = ", ".join(sorted(STRENGTH_PRESETS))
        raise ValueError(f"unknown strength preset {key!r}; choose from: {choices}") from exc
