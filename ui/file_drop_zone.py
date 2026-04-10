from pathlib import Path
from typing import Callable, Optional, Sequence

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QFrame, QLabel, QPushButton, QVBoxLayout


class FileDropZone(QFrame):
    file_selected = pyqtSignal(str)

    def __init__(
        self,
        title: str,
        suffixes: Sequence[str],
        file_filter: str,
        directory_provider: Optional[Callable[[], str]] = None,
    ) -> None:
        super().__init__()
        self.title = title
        self.suffixes = tuple(item.lower() for item in suffixes)
        self.file_filter = file_filter
        self.directory_provider = directory_provider
        self.file_path = ""

        self.setAcceptDrops(True)
        self.setMinimumHeight(210)
        self.setStyleSheet(
            """
            QFrame {
                border: 2px dashed #9fb5cf;
                border-radius: 18px;
                background-color: #f7faff;
            }
            QLabel {
                color: #2f4056;
            }
            QPushButton {
                background-color: #1e6ad8;
                color: white;
                border: none;
                border-radius: 14px;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1859b6;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(title_label)

        self.hint_label = QLabel("拖拽文件到这里，或点击下方按钮选择。")
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setWordWrap(True)
        self.hint_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.hint_label)

        self.path_label = QLabel("未选择文件")
        self.path_label.setAlignment(Qt.AlignCenter)
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("font-size: 13px; color: #5f6f82;")
        layout.addWidget(self.path_label)

        self.choose_button = QPushButton("选择文件")
        self.choose_button.clicked.connect(self._choose_file)
        layout.addWidget(self.choose_button, alignment=Qt.AlignCenter)

    def is_valid(self) -> bool:
        return bool(self.file_path) and Path(self.file_path).is_file()

    def set_file(self, path: str, emit_signal: bool = True) -> bool:
        candidate = Path(path)
        if not candidate.is_file() or not self._is_supported(candidate):
            return False

        self.file_path = str(candidate)
        self.path_label.setText(self.file_path)
        if emit_signal:
            self.file_selected.emit(self.file_path)
        return True

    def _choose_file(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "选择{title}".format(title=self.title),
            self._browse_path(),
            self.file_filter,
        )
        if selected:
            self.set_file(selected)

    def _browse_path(self) -> str:
        if self.directory_provider is None:
            return ""
        current = self.directory_provider() or ""
        path = Path(current)
        if path.is_file():
            return str(path.parent)
        if path.is_dir():
            return str(path)
        return ""

    def _is_supported(self, path: Path) -> bool:
        return path.suffix.lower() in self.suffixes

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            if self._is_supported(Path(url.toLocalFile())):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event) -> None:  # type: ignore[override]
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            candidate = url.toLocalFile()
            if self.set_file(candidate):
                event.acceptProposedAction()
                return
        event.ignore()
