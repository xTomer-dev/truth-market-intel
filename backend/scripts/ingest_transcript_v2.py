from app.db.session import SessionLocal
from app.models.company import Company
from app.models.document import Document
from app.models.speaker_block import SpeakerBlock
from app.services.transcript_parser import split_speaker_blocks


def ingest(company_ticker: str, transcript_text: str) -> None:
    with SessionLocal() as db:
        company = db.query(Company).filter_by(ticker=company_ticker).first()

        if not company:
            print("Company not found")
            return

        document = Document(
            company_id=company.id,
            document_type="earnings_call",
            title="NVDA Earnings Call - Follow-up Quarter",
            raw_text=transcript_text,
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        blocks = split_speaker_blocks(transcript_text)

        for i, block in enumerate(blocks):
            db.add(
                SpeakerBlock(
                    document_id=document.id,
                    speaker=block["speaker"],
                    text=block["text"],
                    block_index=i,
                )
            )

        db.commit()
        print(f"Ingested document_id={document.id} with {len(blocks)} speaker blocks.")


if __name__ == "__main__":
    sample_text = """
CEO: Demand remains strong for AI chips.

CFO: Revenue grew 18 percent year over year.

CEO: We expect capex to increase next quarter.
"""
    ingest("NVDA", sample_text)
