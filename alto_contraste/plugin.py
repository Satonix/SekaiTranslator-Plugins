from sekai_translator.plugins.types.visual import VisualPlugin
from sekai_translator.plugins.visual_types import TextStyle
from sekai_translator.core import TranslationStatus


class AltoContrastePlugin(VisualPlugin):
    id = "alto_contraste"
    name = "Alto Contraste"
    version = "1.0.0"

    def apply(self, context):
        # Nenhum tema global por enquanto
        pass

    def style_table_cell(self, entry, column: str):
        if entry.status == TranslationStatus.IN_PROGRESS:
            return TextStyle(
                background="#747812"
            )

        if entry.status == TranslationStatus.TRANSLATED:
            return TextStyle(
                background="#2A4F31"
            )

        return None







