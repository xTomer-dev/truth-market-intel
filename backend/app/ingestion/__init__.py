from app.ingestion.registry import registry
from app.ingestion.sources.earnings_call_manual import build_manual_earnings_call_document
from app.ingestion.sources.ir_html import build_ir_html_document
from app.ingestion.sources.sec_edgar import build_latest_sec_filing_document
from app.ingestion.sources.url_text import build_url_text_document

registry.register("earnings_call_manual", build_manual_earnings_call_document)
registry.register("url_text", build_url_text_document)
registry.register("ir_html", build_ir_html_document)
registry.register("sec_edgar_latest", build_latest_sec_filing_document)

__all__ = [
    "registry",
    "build_manual_earnings_call_document",
    "build_url_text_document",
    "build_ir_html_document",
    "build_latest_sec_filing_document",
]
