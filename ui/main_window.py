from pathlib import Path

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from converter import ConversionError, ConversionService

from .file_drop_zone import FileDropZone


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.conversion_service = ConversionService()
        self.settings = QSettings("Codex", "TxtToSrtConverter")
        self._build_ui()
        self._restore_recent_file()
        if not self.log_view.toPlainText().strip():
            self._append_log("等待载入 TXT 文件。")

    def _build_ui(self) -> None:
        self.setWindowTitle("TXT 转 SRT 转换器")
        self.setFixedSize(920, 680)
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #edf2f7;
            }
            QWidget {
                font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
            }
            QPushButton {
                background-color: #1459c7;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 20px;
                font-weight: 700;
                padding: 14px 28px;
            }
            QPushButton:hover:enabled {
                background-color: #0f4bac;
            }
            QPushButton:disabled {
                background-color: #a7bbdb;
                color: #edf3fb;
            }
            """
        )

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setContentsMargins(50, 34, 50, 34)
        outer_layout.setSpacing(20)

        self.txt_zone = FileDropZone(
            "TXT 字幕文件",
            (".txt",),
            "Text Files (*.txt)",
            directory_provider=lambda: self._recent_path_for("recent/txt_path"),
        )
        self.txt_zone.file_selected.connect(self._on_txt_selected)
        outer_layout.addWidget(self.txt_zone)

        fps_row = QHBoxLayout()
        fps_row.setSpacing(14)
        fps_label = QLabel("FPS")
        fps_label.setStyleSheet("font-size: 20px; font-weight: 700; color: #30475f;")
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 240)
        self.fps_spin.setValue(self.settings.value("recent/fps", 25, type=int))
        self.fps_spin.setFixedWidth(130)
        self.fps_spin.setStyleSheet(
            """
            QSpinBox {
                font-size: 18px;
                border: 2px solid #b8c8dc;
                border-radius: 12px;
                padding: 8px 10px;
                background: #ffffff;
                color: #2f3e51;
            }
            """
        )
        fps_row.addStretch()
        fps_row.addWidget(fps_label)
        fps_row.addWidget(self.fps_spin)
        fps_row.addStretch()
        outer_layout.addLayout(fps_row)

        log_title = QLabel("预览与日志")
        log_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        log_title.setStyleSheet("font-size: 20px; font-weight: 700; color: #324255;")
        outer_layout.addWidget(log_title)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(220)
        self.log_view.setStyleSheet(
            """
            QPlainTextEdit {
                border: 2px solid #d5deea;
                border-radius: 20px;
                background-color: #fbfdff;
                color: #45576d;
                padding: 16px;
                font-size: 14px;
            }
            """
        )
        outer_layout.addWidget(self.log_view)
        outer_layout.addStretch()

        button_row = QHBoxLayout()
        button_row.addStretch()
        self.convert_button = QPushButton("开始转换")
        self.convert_button.setFixedSize(240, 70)
        self.convert_button.setEnabled(False)
        self.convert_button.clicked.connect(self._select_output_and_convert)
        button_row.addWidget(self.convert_button)
        button_row.addStretch()
        outer_layout.addLayout(button_row)

    def _refresh_convert_button(self) -> None:
        self.convert_button.setEnabled(self.txt_zone.is_valid())

    def _on_txt_selected(self, path: str) -> None:
        self.settings.setValue("recent/txt_path", path)
        self._append_log("已载入 TXT 字幕：{path}".format(path=path))
        self._refresh_convert_button()

    def _select_output_and_convert(self) -> None:
        if not self.txt_zone.is_valid():
            QMessageBox.warning(self, "提示", "请先载入 TXT 字幕文件。")
            return

        txt_path = Path(self.txt_zone.file_path)
        output_directory = self._recent_output_dir() or str(txt_path.parent)
        default_output = Path(output_directory) / "{stem}.srt".format(stem=txt_path.stem)
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择转换后的 SRT 保存位置",
            str(default_output),
            "SRT Files (*.srt)",
        )
        if not output_path:
            return
        if not output_path.lower().endswith(".srt"):
            output_path += ".srt"

        output_file = Path(output_path)
        if output_file.exists():
            reply = QMessageBox.question(
                self,
                "覆盖确认",
                "文件已存在，是否覆盖？\n{path}".format(path=output_file),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        fps = int(self.fps_spin.value())
        self.settings.setValue("recent/fps", fps)
        self.convert_button.setEnabled(False)
        self._append_log(
            "开始转换：\nTXT 文件：{txt}\nFPS：{fps}\n输出路径：{output}".format(
                txt=self.txt_zone.file_path,
                fps=fps,
                output=output_path,
            )
        )

        try:
            result = self.conversion_service.convert(
                txt_path=self.txt_zone.file_path,
                output_srt_path=output_path,
                fps=fps,
            )
        except ConversionError as exc:
            QMessageBox.critical(self, "转换失败", str(exc))
            self._append_log("转换失败：{msg}".format(msg=str(exc)))
            self._refresh_convert_button()
            return
        except Exception as exc:  # pragma: no cover
            QMessageBox.critical(self, "转换失败", "发生了未预期错误：{msg}".format(msg=str(exc)))
            self._append_log("转换失败：发生未预期错误：{msg}".format(msg=str(exc)))
            self._refresh_convert_button()
            return

        self.settings.setValue("recent/output_dir", str(output_file.parent))
        self._refresh_convert_button()

        preview_block = "\n".join(
            "{idx}. {text}".format(idx=index, text=line.replace("\n", " / "))
            for index, line in enumerate(result.preview_lines, start=1)
        )
        warning_lines = list(result.warnings[:10])
        warning_block = "\n".join(warning_lines)
        if len(result.warnings) > 10:
            warning_block += "\n... 共 {count} 条 warning".format(count=len(result.warnings))

        message = "转换完成：已生成 {count} 条字幕，跳过 {skipped} 条异常片段。\n输出文件：{output}".format(
            count=result.cue_count,
            skipped=result.skipped_count,
            output=result.output_path,
        )
        if preview_block:
            message += "\n预览：\n{preview}".format(preview=preview_block)
        if warning_block:
            message += "\nWarnings：\n{warnings}".format(warnings=warning_block)

        self._append_log(message)
        QMessageBox.information(self, "转换完成", message)

    def _restore_recent_file(self) -> None:
        restored = False
        txt_path = self.settings.value("recent/txt_path", "", type=str)
        if txt_path and Path(txt_path).is_file():
            if self.txt_zone.set_file(txt_path, emit_signal=False):
                restored = True
        if restored:
            self._append_log("已恢复最近一次使用的 TXT 文件路径。")
        self._refresh_convert_button()

    def _recent_output_dir(self) -> str:
        recent_dir = self.settings.value("recent/output_dir", "", type=str)
        if recent_dir and Path(recent_dir).is_dir():
            return recent_dir
        return ""

    def _recent_path_for(self, key: str) -> str:
        value = self.settings.value(key, "", type=str)
        if value and Path(value).exists():
            return value
        return self._recent_output_dir()

    def _append_log(self, message: str) -> None:
        current_text = self.log_view.toPlainText().strip()
        combined = "{prev}\n\n{curr}".format(prev=current_text, curr=message).strip() if current_text else message
        self.log_view.setPlainText(combined)
        scrollbar = self.log_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
