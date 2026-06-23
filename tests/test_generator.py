from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageDraw

from cyber_antiquing import AntiquingConfig, generate_antiqued_image, get_preset


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


if __name__ == "__main__":
    unittest.main()
