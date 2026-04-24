from .base import Reporter, ReporterFactory
from .html_reporter import HtmlReporter
from .json_reporter import JsonReporter
from .text_reporter import TextLogReporter


def default_factory() -> ReporterFactory:
    factory = ReporterFactory()
    factory.register("json", JsonReporter)
    factory.register("html", HtmlReporter)
    factory.register("text", TextLogReporter)
    return factory


__all__ = [
    "Reporter",
    "ReporterFactory",
    "HtmlReporter",
    "JsonReporter",
    "TextLogReporter",
    "default_factory",
]
