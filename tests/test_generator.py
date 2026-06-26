from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageDraw

from cyber_antiquing import AntiquingConfig, generate_antiqued_image, generate_antiqued_pil, get_preset, get_strength_preset
from cyber_antiquing.web import create_sample_image, process_image


class GeneratorTests(unittest.TestCase):
    def test_generate_antiqued_image_preserves_size(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            source = temp / "source.png"
            output = temp / "output.jpg"

            image = Image.new("RGB", (96, 64), (240, 240, 240))
            draw = ImageDraw.Draw(image)
            draw.rectangle((8, 8, 60, 38), fill=(220, 40, 60))
            draw.ellipse((44, 20, 86, 56), fill=(40, 90, 220))
            image.save(source)

            result = generate_antiqued_image(
                source,
                output,
                AntiquingConfig(passes=3, seed=123, platforms=("tieba", "wechat")),
            )

            self.assertTrue(output.exists())
            self.assertEqual(3, len(result.steps))
            with Image.open(output) as generated:
                self.assertEqual((96, 64), generated.size)
                self.assertEqual("JPEG", generated.format)

    def test_unknown_platform_raises_clear_error(self):
        with self.assertRaisesRegex(ValueError, "unknown platform preset"):
            get_preset("not-a-platform")

    def test_generate_antiqued_pil_returns_image_result(self):
        source = Image.new("RGB", (80, 50), (220, 220, 210))
        result = generate_antiqued_pil(source, AntiquingConfig(passes=2, seed=9))

        self.assertEqual((80, 50), result.image.size)
        self.assertEqual(2, len(result.steps))

    def test_strength_preset_builds_config(self):
        preset = get_strength_preset("heavy")
        config = preset.to_config(seed=11)

        self.assertEqual(9, config.passes)
        self.assertGreater(config.intensity, 1.0)
        self.assertEqual(11, config.seed)

    def test_web_process_image_uses_presets(self):
        source = create_sample_image()
        output, summary = process_image(
            source,
            "light",
            2,
            0.8,
            ["wechat"],
            False,
            False,
            True,
            True,
            123,
        )

        self.assertEqual(source.size, output.size)
        self.assertIn("passes=2", summary)
        self.assertIn("wechat", summary)


if __name__ == "__main__":
    unittest.main()
