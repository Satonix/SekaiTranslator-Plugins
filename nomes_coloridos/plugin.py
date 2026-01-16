from pathlib import Path
import json

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QColorDialog,
    QHBoxLayout,
)
from PySide6.QtCore import QTimer

from sekai_translator.plugins.types.visual import VisualPlugin
from sekai_translator.plugins.visual_types import TextStyle


# ============================================================
# Config Widget (INALTERADO NA ESSÊNCIA)
# ============================================================

class SpeakerColorsConfig(QWidget):
    def __init__(self, plugin, context):
        super().__init__()

        self.plugin = plugin
        self.context = context
        self.project_path: Path | None = None

        layout = QVBoxLayout(self)

        title = QLabel("Cores por personagem (projeto atual)")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)

        self.project_label = QLabel()
        layout.addWidget(self.project_label)

        self.list = QListWidget()
        layout.addWidget(self.list)

        btn_row = QHBoxLayout()
        self.btn_color = QPushButton("Alterar cor")
        self.btn_remove = QPushButton("Remover cor")
        btn_row.addWidget(self.btn_color)
        btn_row.addWidget(self.btn_remove)
        layout.addLayout(btn_row)

        self.btn_color.clicked.connect(self._change_color)
        self.btn_remove.clicked.connect(self._remove_color)

        QTimer.singleShot(0, self._refresh)

    # --------------------------------------------------------

    def _refresh(self):
        self.list.clear()

        project = self.context.current_project
        if not project:
            self.project_label.setText("Nenhum projeto aberto.")
            self.list.addItem("(Nenhum projeto aberto)")
            self.list.setEnabled(False)
            return

        self.project_path = Path(project.root_path)
        self.project_label.setText(f"Projeto: {project.name}")

        self.plugin.load_colors(self.project_path)

        speakers = self.plugin.collect_speakers(project)

        if not speakers:
            self.list.addItem("(Nenhum personagem encontrado no projeto)")
            self.list.setEnabled(False)
            return

        self.list.setEnabled(True)

        for speaker in speakers:
            color = self.plugin.colors.get(speaker, "(sem cor)")
            self.list.addItem(f"{speaker} → {color}")

    # --------------------------------------------------------

    def _change_color(self):
        if not self.project_path:
            return

        item = self.list.currentItem()
        if not item:
            return

        speaker = item.text().split(" → ")[0]
        current = self.plugin.colors.get(speaker, "#ffffff")

        color = QColorDialog.getColor(
            parent=self,
            title=f"Escolher cor para {speaker}",
        )

        if not color.isValid():
            return

        self.plugin.colors[speaker] = color.name()
        self.plugin.save_colors(self.project_path)
        self._refresh()

    # --------------------------------------------------------

    def _remove_color(self):
        if not self.project_path:
            return

        item = self.list.currentItem()
        if not item:
            return

        speaker = item.text().split(" → ")[0]

        if speaker in self.plugin.colors:
            del self.plugin.colors[speaker]
            self.plugin.save_colors(self.project_path)
            self._refresh()


# ============================================================
# Plugin Visual (NOVO CONTRATO)
# ============================================================

class Plugin(VisualPlugin):
    id = "nomes_coloridos"
    name = "Nomes Coloridos"
    version = "1.0.0"

    def __init__(self):
        self.colors: dict[str, str] = {}
        self.context = None

    # --------------------------------------------------------
    # Lifecycle
    # --------------------------------------------------------

    def apply(self, context):
        self.context = context

        project = context.current_project
        if project:
            self.load_colors(Path(project.root_path))

    def on_unload(self, context):
        self.colors.clear()
        context.refresh_visuals()

    # --------------------------------------------------------
    # Hooks visuais (ESSÊNCIA DO PLUGIN)
    # --------------------------------------------------------

    def style_table_cell(self, entry, column: str):
        speaker = entry.context.get("speaker")
        if not speaker:
            return None

        color = self.colors.get(speaker)
        if not color:
            return None

        if column == "speaker":
            return TextStyle(color=color, bold=True)

        if column in {"original", "translation"}:
            return TextStyle(color=color)

        return None

    def style_original_text(self, entry):
        speaker = entry.context.get("speaker")
        if not speaker:
            return None

        color = self.colors.get(speaker)
        if color:
            return TextStyle(color=color)
        return None

    def style_translation_text(self, entry):
        speaker = entry.context.get("speaker")
        if not speaker:
            return None

        color = self.colors.get(speaker)
        if color:
            return TextStyle(color=color)
        return None

    # --------------------------------------------------------
    # Config GUI
    # --------------------------------------------------------

    def has_config(self) -> bool:
        return True

    def create_config_widget(self, context):
        return SpeakerColorsConfig(self, context)

    # --------------------------------------------------------
    # Persistence
    # --------------------------------------------------------

    def _config_path(self, project_path: Path) -> Path:
        return (
            project_path
            / ".sekai"
            / "plugins"
            / "nomes_coloridos.json"
        )

    def load_colors(self, project_path: Path):
        path = self._config_path(project_path)
        self.colors.clear()

        if path.exists():
            try:
                self.colors.update(
                    json.loads(path.read_text(encoding="utf-8"))
                )
            except Exception:
                pass

        if self.context:
            self.context.refresh_visuals()

    def save_colors(self, project_path: Path):
        path = self._config_path(project_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(
            json.dumps(self.colors, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # --------------------------------------------------------
    # Speaker discovery
    # --------------------------------------------------------

    def collect_speakers(self, project):
        speakers = set()

        for entries in project.files.values():
            for entry in entries:
                speaker = entry.context.get("speaker")
                if not speaker:
                    continue

                speaker = speaker.strip()

                if speaker.lower() in {
                    "alguém",
                    "voz de alguém",
                    "unknown",
                    "???",
                }:
                    continue

                speakers.add(speaker)

        return sorted(speakers)
