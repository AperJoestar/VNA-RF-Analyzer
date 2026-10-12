"""Feature mixins that make up the main window."""
from rfanalyzer.gui.mixins.appearance import AppearanceMixin
from rfanalyzer.gui.mixins.files import FileDataMixin
from rfanalyzer.gui.mixins.gallery import GalleryMixin
from rfanalyzer.gui.mixins.analysis import AnalysisMixin
from rfanalyzer.gui.mixins.params_tab import ParamsTabMixin
from rfanalyzer.gui.mixins.absorption_tab import AbsorptionTabMixin
from rfanalyzer.gui.mixins.trend_tab import TrendTabMixin
from rfanalyzer.gui.mixins.exports import ExportMixin

__all__ = [
    "AppearanceMixin",
    "FileDataMixin",
    "GalleryMixin",
    "AnalysisMixin",
    "ParamsTabMixin",
    "AbsorptionTabMixin",
    "TrendTabMixin",
    "ExportMixin",
]
