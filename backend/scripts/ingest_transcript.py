import sys

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.speaker_block import SpeakerBlock
from app.models.company import Company
from app.services.transcript_parser import split_speaker_blocks


def ingest(company_ticker, transcript_text):

    with SessionLocal() as db:

        company = db.query(Company).filter_by(ticker=company_ticker).first()

        if not company:
            print("Company not found")
            return

        document = Document(
            company_id=company.id,
            document_type="earnings_call",
            raw_text=transcript_text
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        blocks = split_speaker_blocks(transcript_text)

        for i, block in enumerate(blocks):

            db_block = SpeakerBlock(
                document_id=document.id,
                speaker=block["speaker"],
                text=block["text"],
                block_index=i
            )

            db.add(db_block)

        db.commit()

        print(f"Ingested {len(blocks)} speaker blocks")


if __name__ == "__main__":

    sample_text = """
CEO: Demand remains strong for AI chips.

CFO: Revenue grew 20 percent year over year.

CEO: We expect margins to improve next quarter.
"""

    ingest("NVDA", sample_text)
