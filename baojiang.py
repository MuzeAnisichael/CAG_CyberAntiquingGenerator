from PIL import Image, ImageDraw
import random
import io


def pixelate_image(image, pixelation_factor):
    width, height = image.size
    pixel_size = pixelation_factor

    for y in range(0, height, pixel_size):
        for x in range(0, width, pixel_size):
            box = (x, y, x + pixel_size, y + pixel_size)
            region = image.crop(box)
            average_color = region.reduce(2).getpixel((0, 0))
            image.paste(average_color, box)

def add_noise(image, noise_factor):
    width, height = image.size
    pixels = image.load()

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            noise = int(noise_factor * random.randint(-255, 255))  # Convert noise to an integer
            pixels[x, y] = (
                max(0, min(r + noise, 255)),
                max(0, min(g + noise, 255)),
                max(0, min(b + noise, 255))
            )



def color_shift(image, color_shift_factor):
    r_shift = int(color_shift_factor * random.randint(-255, 255))
    g_shift = int(color_shift_factor * random.randint(-255, 255))
    b_shift = int(color_shift_factor * random.randint(-255, 255))
    lut = [i + r_shift for i in range(256)] + [i + g_shift for i in range(256)] + [i + b_shift for i in range(256)]
    image = image.point(lut)
    return image

def apply_jpeg_compression(image, compression_quality):
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=compression_quality)
    return Image.open(buffer)

def apply_watermark(image, watermark_text):
    draw = ImageDraw.Draw(image)
    text_width, text_height = draw.textsize(watermark_text)
    width, height = image.size
    text_x = width - text_width - 10
    text_y = height - text_height - 10
    draw.text((text_x, text_y), watermark_text, fill=(255, 255, 255, 128))
    return image

def generate_distorted_image(input_path, output_path, pixelation_factor, noise_factor, color_shift_factor,
                             compression_quality, repeat_compression_times, format_conversion, add_watermark):
    image = Image.open(input_path)

    # 重复压缩
    for _ in range(repeat_compression_times):
        image = apply_jpeg_compression(image, compression_quality)

    # 格式转换
    if format_conversion == "JPEG":
        image = apply_jpeg_compression(image, compression_quality)

    # 添加水印
    if add_watermark != False:
        watermark_text = add_watermark
        image = apply_watermark(image, watermark_text)

    # 像素化
    pixelate_image(image, pixelation_factor)

    # 添加噪声
    add_noise(image, noise_factor)

    # 颜色偏移
    image = color_shift(image, color_shift_factor)

    # 保存图像
    image.save(output_path)
    image.show()

if __name__ == "__main__":

    # 输入图像路径和输出图像路径
    input_image_path = "input_image2.jpg"
    output_image_path = "distorted_image2.jpg"

    # 参数调整
    # 控制像素化程度
    pixelation_factor = 5
    # 噪声强度
    noise_factor = 0.01
    # 颜色偏移强度
    color_shift_factor = 0.5
    # 压缩质量（0-100）
    compression_quality = 10
    # 重复压缩次数
    repeat_compression_times = 5
    # 格式转换
    format_conversion = "JPEG"
    # 添加水印
    add_watermark = "baidutieba"

    generate_distorted_image(input_image_path, output_image_path, pixelation_factor, noise_factor, color_shift_factor,
                             compression_quality, repeat_compression_times, format_conversion, add_watermark)



