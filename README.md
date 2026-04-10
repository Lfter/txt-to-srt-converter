# txt-to-srt-converter

将形如 `HH:MM:SS:FF - HH:MM:SS:FF` 的 TXT 字幕稿转换为标准 SRT 文件。

项目提供一个基于 `PyQt5` 的桌面工具，支持选择单个 TXT 文件、设置 FPS、导出 SRT，并在界面中显示转换日志与预览。

## 功能概览

- 选择单个 `.txt` 字幕源文件进行转换
- FPS 默认 `25`，可手动修改（支持 1-240）
- 自动解析时间码和字幕正文
- 容错跳过异常片段并记录 warning
- 输出标准 SRT（UTF-8 编码）

## 本地开发安装

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-build.txt
```

## 源码运行

```bash
.venv/bin/python main.py
```

## 测试

```bash
.venv/bin/pytest
```

## 打包 macOS App

```bash
./packaging/macos/build_macos_app.sh
```

构建完成后产物在：

- `dist/txt_to_srt.app`

## TXT 输入格式

每个字幕块使用空行分隔，推荐结构如下：

```text
00:00:02:14 - 00:00:03:02
V1, 1
谢谢
```

- 第一行：时间范围（必需）
- 第二行：轨道标记（可选，形如 `V1, 1`）
- 后续行：字幕正文（至少一行）

当块格式异常（例如时间行无效、结束时间不晚于开始时间、正文为空）时，程序会跳过该块并在日志中提示。
