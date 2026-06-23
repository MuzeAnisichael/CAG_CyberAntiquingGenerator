# CAG Cyber Antiquing Generator

电子包浆生成器。它用 Python 模拟图片或表情包在贴吧、微博、QQ、微信等平台反复上传、下载、转发后产生的压缩失真、层叠水印、色偏、噪声和分辨率劣化。

项目目标不是普通滤镜，而是快速制造“被很多平台转了很多手”的网络图片质感。

## 功能

- 选择包浆次数：每一次代表一次平台上传/下载链路
- 随机平台包浆：每轮随机经过贴吧、微博、QQ、微信等平台预设
- 固定平台链路：按你指定的平台顺序循环处理
- 随机或固定方法：可以随机采样压缩参数，也可以使用各平台预设的中位参数
- 真实重编码：JPEG/WebP/PNG8 多次 round-trip，包含 JPEG 4:2:0 色度抽样
- 平台处理模拟：缩放再采样、调色、锐化/模糊、轻量噪声
- 层叠水印：每轮压缩前叠加平台水印，使水印也被后续压缩继续劣化
- 可复现随机：支持 `--seed`
- 保留旧实现：原始脚本已保存为 `baojiang(old).py`
- 保留兼容入口：仍可运行 `python baojiang.py`

## 安装

```bash
pip install -r requirements.txt
```

开发模式安装：

```bash
pip install -e .
```

## 快速使用

只安装依赖、不安装包时，可以用兼容入口：

```bash
python baojiang.py input.jpg output.jpg --passes 8 --seed 42
```

如果已经执行过 `pip install -e .`，可以使用模块入口：

```bash
python -m cyber_antiquing input.jpg output.jpg --passes 8 --seed 42
```

也可以使用命令行入口：

```bash
cyber-antiquing input.jpg output.jpg --passes 8 --seed 42
```

## 常用参数

列出平台预设：

```bash
python -m cyber_antiquing --list-platforms
```

随机平台链路，包浆 10 次：

```bash
python -m cyber_antiquing input.jpg output.jpg -n 10 --intensity 1.3
```

固定平台顺序，例如先贴吧再微博再微信，循环 9 次：

```bash
python -m cyber_antiquing input.jpg output.jpg -n 9 -p tieba -p weibo -p wechat --no-random-platforms
```

固定平台与固定方法，便于对比实验：

```bash
python -m cyber_antiquing input.jpg output.jpg -n 6 --no-random-platforms --no-random-methods
```

关闭水印，只模拟压缩和失真：

```bash
python -m cyber_antiquing input.jpg output.jpg -n 6 --no-watermark
```

不把最终图片拉回原始尺寸：

```bash
python -m cyber_antiquing input.jpg output.jpg -n 6 --no-keep-size
```

## 平台预设

当前内置平台：

- `tieba`
- `weibo`
- `qq`
- `wechat`
- `douyin`
- `rednote`

每个平台预设包含自己的压缩格式、压缩质量范围、最大边长、二次缩放范围、噪声、色偏、锐化/模糊和水印风格。实际每轮会从范围中采样，因此同一张图每次生成都可能不同；使用 `--seed` 可以复现结果。

## Python API

```python
from cyber_antiquing import AntiquingConfig, generate_antiqued_image

config = AntiquingConfig(
    passes=8,
    platforms=("tieba", "weibo", "qq", "wechat"),
    random_platforms=True,
    random_methods=True,
    seed=42,
    intensity=1.2,
)

result = generate_antiqued_image("input.jpg", "output.jpg", config)
print(result.steps)
```

## 测试

Windows PowerShell:

```powershell
$env:PYTHONPATH="src"; python -m unittest discover -s tests
```

Linux/macOS:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## 兼容说明

旧版本脚本已保存为 `baojiang(old).py`。新的 `baojiang.py` 是兼容包装器，支持旧函数名，也可以直接作为 CLI 使用。

新代码建议直接使用：

```bash
python -m cyber_antiquing input.jpg output.jpg
```
