"""
Deterministic synthetic seed for ASTS (AST SpaceMobile).

random.seed(42) → same DB state every run.
Idempotent: get-or-create semantics throughout.

Coverage:
  - 1 company, 2 persons, 2 institutions
  - 5 documents, 5 events
  - 5 canonical threads
  - 18 claims (with EvidenceSpans)
  - 17 thread states
  - 8 state deltas
  - 11 transitions
  - 5 market reactions
"""

import asyncio
import json
import pathlib
import random
import sys
import uuid
from datetime import datetime

# Allow running as script from backend/
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.claim import Claim
from app.models.company import Company
from app.models.document import Document
from app.models.wedge_core import (
    DeltaDirectionEnum,
    DocumentTypeEnum,
    EvidenceSpan,
    EstimateRevisionEnum,
    EventTypeEnum,
    HorizonEnum,
    InstitutionTypeEnum,
    Institution,
    MarketReaction,
    NarrativeThread,
    Person,
    PersonTypeEnum,
    PolarityEnum,
    SectorEnum,
    StateDelta,
    ThreadState,
    ThreadStatusEnum,
    Transition,
    TransitionMechanismEnum,
    TransitionSpeedEnum,
    WedgeEvent,
)

# ── Deterministic RNG ────────────────────────────────────────────────────────

RNG = random.Random(42)

PROJ_ROOT = pathlib.Path(__file__).parent.parent.parent
SOURCE_TEXTS_PATH = PROJ_ROOT / "data" / "synthetic" / "asts" / "source_texts.json"


def _uuid() -> uuid.UUID:
    return uuid.UUID(bytes=bytes(RNG.getrandbits(8) for _ in range(16)), version=4)


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _get_or_create_company(db) -> Company:
    r = await db.execute(select(Company).where(Company.ticker == "ASTS"))
    obj = r.scalars().first()
    if obj:
        return obj
    obj = Company(
        ticker="ASTS",
        name="AST SpaceMobile",
        sector="telecommunications",
        industry="Satellite Communications",
        sector_enum=SectorEnum.telecommunications,
    )
    db.add(obj)
    await db.flush()
    return obj


async def _get_or_create_person(db, name, type_, role) -> Person:
    r = await db.execute(select(Person).where(Person.name == name))
    obj = r.scalars().first()
    if obj:
        return obj
    obj = Person(id=_uuid(), name=name, type=type_, role=role)
    db.add(obj)
    await db.flush()
    return obj


async def _get_or_create_institution(db, name, type_) -> Institution:
    r = await db.execute(select(Institution).where(Institution.name == name))
    obj = r.scalars().first()
    if obj:
        return obj
    obj = Institution(id=_uuid(), name=name, type=type_)
    db.add(obj)
    await db.flush()
    return obj


async def _get_or_create_document(db, company_id, doc_key, title, period, wc_type, published_at, raw_text_path, raw_text="") -> Document:
    r = await db.execute(
        select(Document).where(Document.external_id == f"synthetic_{doc_key}")
    )
    obj = r.scalars().first()
    if obj:
        return obj
    obj = Document(
        company_id=company_id,
        document_type=wc_type.value,
        # wc_type omitted: SQLAlchemy sends enum.name not enum.value for non-matching enums
        title=title,
        period=period,
        external_id=f"synthetic_{doc_key}",
        published_at=published_at,
        raw_text_path=str(raw_text_path),
        raw_text=raw_text,
        ingestion_source="synthetic_seed",
    )
    db.add(obj)
    await db.flush()
    return obj


async def _get_or_create_thread(db, company_id, name, kpi_label=None) -> NarrativeThread:
    r = await db.execute(
        select(NarrativeThread).where(
            NarrativeThread.company_id == company_id,
            NarrativeThread.name == name,
        )
    )
    obj = r.scalars().first()
    if obj:
        return obj
    from app.core.vocabulary import kpi_label_for
    obj = NarrativeThread(
        id=_uuid(),
        name=name,
        company_id=company_id,
        status=ThreadStatusEnum.active,
        description="",
        kpi_label=kpi_label or kpi_label_for(name),
        transition_threshold=0.20,
    )
    db.add(obj)
    await db.flush()
    return obj


async def _get_or_create_thread_state(
    db, thread_id, time_period, sentiment_score, summary, document_id=None
) -> ThreadState:
    r = await db.execute(
        select(ThreadState).where(
            ThreadState.narrative_thread_id == thread_id,
            ThreadState.time_period == time_period,
        )
    )
    obj = r.scalars().first()
    if obj:
        return obj
    obj = ThreadState(
        id=_uuid(),
        narrative_thread_id=thread_id,
        time_period=time_period,
        sentiment_score=sentiment_score,
        summary=summary,
        document_id=document_id,
    )
    db.add(obj)
    await db.flush()
    return obj


async def _get_or_create_claim(db, company_id, thread_id, span_id, verbatim, summary, polarity, confidence, horizon) -> Claim:
    r = await db.execute(
        select(Claim).where(
            Claim.company_id == company_id,
            Claim.verbatim == verbatim,
        )
    )
    obj = r.scalars().first()
    if obj:
        return obj
    obj = Claim(
        company_id=company_id,
        narrative_thread_id=thread_id,
        evidence_span_id=span_id,
        claim_text=verbatim,
        verbatim=verbatim,
        summary=summary,
        polarity=polarity.value,
        wc_polarity=polarity,
        confidence=confidence,
        horizon=horizon,
        extraction_method="synthetic_seed",
    )
    db.add(obj)
    await db.flush()
    return obj


async def _get_or_create_state_delta(db, thread_id, claim_id, dimension, direction, magnitude, thread_state_id) -> StateDelta:
    r = await db.execute(
        select(StateDelta).where(
            StateDelta.narrative_thread_id == thread_id,
            StateDelta.dimension == dimension,
            StateDelta.modifies_thread_state_id == thread_state_id,
        )
    )
    obj = r.scalars().first()
    if obj:
        return obj
    obj = StateDelta(
        id=_uuid(),
        narrative_thread_id=thread_id,
        claim_id=claim_id,
        dimension=dimension,
        direction=direction,
        magnitude=magnitude,
        modifies_thread_state_id=thread_state_id,
    )
    db.add(obj)
    await db.flush()
    return obj


async def _get_or_create_transition(
    db, thread_id, from_state_id, to_state_id,
    mechanism, speed, confidence, summary, time_period,
    person_id=None, institution_id=None
) -> Transition:
    r = await db.execute(
        select(Transition).where(
            Transition.from_thread_state_id == from_state_id,
            Transition.to_thread_state_id == to_state_id,
        )
    )
    obj = r.scalars().first()
    if obj:
        return obj
    obj = Transition(
        id=_uuid(),
        narrative_thread_id=thread_id,
        from_thread_state_id=from_state_id,
        to_thread_state_id=to_state_id,
        mechanism=mechanism,
        speed=speed,
        confidence=confidence,
        summary=summary,
        time_period=time_period,
        attributed_to_person_id=person_id,
        attributed_to_institution_id=institution_id,
    )
    db.add(obj)
    await db.flush()
    return obj


async def _get_or_create_market_reaction(
    db, company_id, transition_id, reacted_at, price_move_pct,
    volume_vs_avg, sentiment_score, options_iv_spike, call_put_ratio,
    estimate_revision_direction
) -> MarketReaction:
    r = await db.execute(
        select(MarketReaction).where(MarketReaction.transition_id == transition_id)
    )
    obj = r.scalars().first()
    if obj:
        return obj
    obj = MarketReaction(
        id=_uuid(),
        company_id=company_id,
        transition_id=transition_id,
        reacted_at=reacted_at,
        price_move_pct=price_move_pct,
        volume_vs_avg=volume_vs_avg,
        sentiment_score=sentiment_score,
        options_iv_spike=options_iv_spike,
        call_put_ratio=call_put_ratio,
        estimate_revision_direction=estimate_revision_direction,
    )
    db.add(obj)
    await db.flush()
    return obj


# ── Main seed function ───────────────────────────────────────────────────────


async def seed():
    # Load source texts
    source_texts = json.loads(SOURCE_TEXTS_PATH.read_text())
    texts_by_key = {t["doc_key"]: t for t in source_texts}

    # Write raw text files
    for st in source_texts:
        p = PROJ_ROOT / "data" / "synthetic" / "asts" / f"{st['doc_key']}.txt"
        p.write_text(st["text"])

    async with AsyncSessionLocal() as db:
        # ── Company ──────────────────────────────────────────────────────────
        company = await _get_or_create_company(db)
        print(f"  company: ASTS id={company.id}")

        # ── Persons ──────────────────────────────────────────────────────────
        ceo = await _get_or_create_person(
            db, "Abel Avellan", PersonTypeEnum.executive, "Chairman & CEO"
        )
        cfo = await _get_or_create_person(
            db, "Sean Wallace", PersonTypeEnum.executive, "Chief Financial Officer"
        )

        # ── Institutions ─────────────────────────────────────────────────────
        att = await _get_or_create_institution(
            db, "AT&T", InstitutionTypeEnum.carrier
        )
        verizon = await _get_or_create_institution(
            db, "Verizon", InstitutionTypeEnum.carrier
        )

        # ── Documents & Events ───────────────────────────────────────────────
        docs = {}
        events = {}

        doc_specs = [
            ("q1_2024_earnings", "Q1-2024", DocumentTypeEnum.earnings_call,
             datetime(2024, 5, 10), EventTypeEnum.earnings_release,
             "Q1 2024 Earnings Release"),
            ("q2_2024_earnings", "Q2-2024", DocumentTypeEnum.earnings_call,
             datetime(2024, 8, 14), EventTypeEnum.earnings_release,
             "Q2 2024 Earnings Release"),
            ("q3_2024_8k_fcc", "Q3-2024", DocumentTypeEnum.eight_k,
             datetime(2024, 11, 5), EventTypeEnum.regulatory_filing,
             "FCC 850 MHz Waiver Received"),
            ("q4_2024_earnings", "Q4-2024", DocumentTypeEnum.earnings_call,
             datetime(2025, 2, 28), EventTypeEnum.earnings_release,
             "Q4 2024 Earnings Release"),
            ("q1_2025_earnings", "Q1-2025", DocumentTypeEnum.earnings_call,
             datetime(2025, 5, 9), EventTypeEnum.earnings_release,
             "Q1 2025 Earnings Release"),
        ]

        for doc_key, period, wc_type, pub_date, evt_type, evt_name in doc_specs:
            txt_path = PROJ_ROOT / "data" / "synthetic" / "asts" / f"{doc_key}.txt"
            raw_text = texts_by_key[doc_key]["text"]
            doc = await _get_or_create_document(
                db, company.id, doc_key,
                texts_by_key[doc_key]["title"],
                period, wc_type, pub_date, txt_path,
                raw_text=raw_text,
            )
            docs[doc_key] = doc

            # Event
            r = await db.execute(
                select(WedgeEvent).where(
                    WedgeEvent.company_id == company.id,
                    WedgeEvent.name == evt_name,
                )
            )
            evt = r.scalars().first()
            if not evt:
                evt = WedgeEvent(
                    id=_uuid(),
                    company_id=company.id,
                    name=evt_name,
                    type=evt_type,
                    occurred_at=pub_date,
                )
                db.add(evt)
                await db.flush()
            events[doc_key] = evt

        # ── Threads ──────────────────────────────────────────────────────────
        t_capital = await _get_or_create_thread(db, company.id, "Capital Adequacy & Dilution Risk")
        t_tech = await _get_or_create_thread(db, company.id, "Technical Feasibility")
        t_carrier = await _get_or_create_thread(db, company.id, "Carrier & Partner Moat")
        t_regulatory = await _get_or_create_thread(db, company.id, "Regulatory & Spectrum Risk")
        t_commercial = await _get_or_create_thread(db, company.id, "Commercial Launch Readiness")

        thread_list = [t_capital, t_tech, t_carrier, t_regulatory, t_commercial]
        for t in thread_list:
            print(f"  thread: {t.name!r} id={t.id}")

        # ── Evidence Spans ───────────────────────────────────────────────────
        # We'll create spans as we define claims below

        async def _span(doc_key, text, start, end, speaker, section) -> EvidenceSpan:
            doc = docs[doc_key]
            r = await db.execute(
                select(EvidenceSpan).where(
                    EvidenceSpan.document_id == doc.id,
                    EvidenceSpan.char_offset_start == start,
                )
            )
            obj = r.scalars().first()
            if obj:
                return obj
            obj = EvidenceSpan(
                id=_uuid(),
                document_id=doc.id,
                text=text,
                char_offset_start=start,
                char_offset_end=end,
                speaker=speaker,
                section=section,
            )
            db.add(obj)
            await db.flush()
            return obj

        # ── Claims (18 total) ─────────────────────────────────────────────────
        # Capital thread claims
        span_c1 = await _span("q1_2024_earnings",
            "Cash runway stands at approximately 14 months at current burn rate of $28 million per quarter.",
            394, 489, "Sean Wallace", "Financial Update")
        c1 = await _get_or_create_claim(db, company.id, t_capital.id, span_c1.id,
            span_c1.text,
            "14-month cash runway at $28M/quarter burn rate indicates near-term financing pressure.",
            PolarityEnum.cautious, 0.88, HorizonEnum.near_term)

        span_c2 = await _span("q2_2024_earnings",
            "Cash position improved following our $200 million convertible note offering, extending runway to 22 months.",
            195, 295, "Sean Wallace", "Financial Update")
        c2 = await _get_or_create_claim(db, company.id, t_capital.id, span_c2.id,
            span_c2.text,
            "$200M convertible note extends runway to 22 months, materially improving liquidity position.",
            PolarityEnum.positive, 0.92, HorizonEnum.near_term)

        span_c3 = await _span("q2_2024_earnings",
            "Burn rate increased to $34 million per quarter reflecting accelerated constellation build.",
            296, 381, "Sean Wallace", "Financial Update")
        c3 = await _get_or_create_claim(db, company.id, t_capital.id, span_c3.id,
            span_c3.text,
            "Burn rate stepped up to $34M/quarter as constellation build accelerates.",
            PolarityEnum.cautious, 0.85, HorizonEnum.near_term)

        span_c4 = await _span("q1_2025_earnings",
            "Cash burn increased to $44 million per quarter as we scale ground operations.",
            175, 255, "Sean Wallace", "Financial Update")
        c4 = await _get_or_create_claim(db, company.id, t_capital.id, span_c4.id,
            span_c4.text,
            "Burn rate increases to $44M/quarter raising near-term financing concerns.",
            PolarityEnum.negative, 0.87, HorizonEnum.near_term)

        span_c5 = await _span("q1_2025_earnings",
            "we are evaluating additional financing to ensure runway through Block 3 constellation completion.",
            256, 352, "Abel Avellan", "Strategic Update")
        c5 = await _get_or_create_claim(db, company.id, t_capital.id, span_c5.id,
            span_c5.text,
            "Company signaling additional dilutive financing needed for Block 3 completion.",
            PolarityEnum.cautious, 0.82, HorizonEnum.medium_term)

        # Technical thread claims
        span_t1 = await _span("q1_2024_earnings",
            "our technical team has validated peak throughput of 52 Mbps per satellite.",
            332, 393, "Abel Avellan", "Technical Update")
        t1 = await _get_or_create_claim(db, company.id, t_tech.id, span_t1.id,
            span_t1.text,
            "52 Mbps peak throughput validated — first proof of commercial-grade performance.",
            PolarityEnum.positive, 0.91, HorizonEnum.immediate)

        span_t2 = await _span("q2_2024_earnings",
            "Peak throughput testing achieved 64 Mbps on latest generation hardware.",
            382, 447, "Abel Avellan", "Technical Update")
        t2 = await _get_or_create_claim(db, company.id, t_tech.id, span_t2.id,
            span_t2.text,
            "Throughput improved 23% quarter-over-quarter to 64 Mbps with Block 2 hardware.",
            PolarityEnum.positive, 0.93, HorizonEnum.immediate)

        span_t3 = await _span("q1_2025_earnings",
            "Technical performance strong: average throughput 58 Mbps, 99.2% uptime.",
            353, 415, "Abel Avellan", "Operational Update")
        t3 = await _get_or_create_claim(db, company.id, t_tech.id, span_t3.id,
            span_t3.text,
            "Average throughput 58 Mbps at 99.2% uptime — solid in-service performance.",
            PolarityEnum.positive, 0.89, HorizonEnum.immediate)

        # Carrier thread claims
        span_k1 = await _span("q1_2024_earnings",
            "AT&T and Verizon have confirmed expanded pilot agreements covering 35 million subscribers.",
            205, 293, "Abel Avellan", "Commercial Update")
        k1 = await _get_or_create_claim(db, company.id, t_carrier.id, span_k1.id,
            span_k1.text,
            "AT&T and Verizon expand pilots to 35M subscribers — carrier moat expanding.",
            PolarityEnum.positive, 0.90, HorizonEnum.near_term)

        span_k2 = await _span("q2_2024_earnings",
            "AT&T has signed a definitive commercial agreement and Verizon remains in final contract negotiations.",
            98, 196, "Abel Avellan", "Commercial Update")
        k2 = await _get_or_create_claim(db, company.id, t_carrier.id, span_k2.id,
            span_k2.text,
            "AT&T signs definitive commercial agreement; Verizon in final negotiations — key moat validated.",
            PolarityEnum.positive, 0.94, HorizonEnum.immediate)

        span_k3 = await _span("q4_2024_earnings",
            "Verizon commercial agreement signed December 2024. Vodafone signed an MOU for European markets.",
            89, 163, "Abel Avellan", "Commercial Update")
        k3 = await _get_or_create_claim(db, company.id, t_carrier.id, span_k3.id,
            span_k3.text,
            "Verizon signed and Vodafone MOU — carrier count expanding internationally.",
            PolarityEnum.positive, 0.92, HorizonEnum.near_term)

        span_k4 = await _span("q1_2025_earnings",
            "Carrier concentration risk: AT&T represents 78% of current revenue.",
            253, 311, "Sean Wallace", "Risk Factors")
        k4 = await _get_or_create_claim(db, company.id, t_carrier.id, span_k4.id,
            span_k4.text,
            "AT&T concentration at 78% of revenue represents significant customer concentration risk.",
            PolarityEnum.cautious, 0.86, HorizonEnum.near_term)

        # Regulatory thread claims
        span_r1 = await _span("q2_2024_earnings",
            "Spectrum interference risk in the 850 MHz band remains a regulatory concern pending FCC ruling expected Q4 2024.",
            448, 562, "Abel Avellan", "Risk Factors")
        r1 = await _get_or_create_claim(db, company.id, t_regulatory.id, span_r1.id,
            span_r1.text,
            "FCC 850 MHz ruling pending; spectrum interference risk is primary regulatory overhang.",
            PolarityEnum.negative, 0.88, HorizonEnum.near_term)

        span_r2 = await _span("q3_2024_8k_fcc",
            "AST SpaceMobile announced today that it has received a conditional waiver from the FCC to operate its direct-to-device satellite service in the 850 MHz band with power limits of -174 dBm/Hz.",
            0, 187, "Company IR", "Press Release")
        r2 = await _get_or_create_claim(db, company.id, t_regulatory.id, span_r2.id,
            span_r2.text,
            "FCC conditional waiver received for 850 MHz operations — primary regulatory risk resolved.",
            PolarityEnum.positive, 0.96, HorizonEnum.immediate)

        span_r3 = await _span("q3_2024_8k_fcc",
            "The company believes this ruling will accelerate carrier negotiations and reduce spectrum-related risk materially.",
            285, 382, "Company IR", "Press Release")
        r3 = await _get_or_create_claim(db, company.id, t_regulatory.id, span_r3.id,
            span_r3.text,
            "FCC waiver expected to accelerate carrier negotiations and materially de-risk regulatory timeline.",
            PolarityEnum.positive, 0.87, HorizonEnum.near_term)

        # Commercial thread claims
        span_m1 = await _span("q2_2024_earnings",
            "we remain on track for commercial launch to general consumers by mid-2025.",
            563, 632, "Abel Avellan", "Guidance")
        m1 = await _get_or_create_claim(db, company.id, t_commercial.id, span_m1.id,
            span_m1.text,
            "Management reaffirms mid-2025 commercial launch timeline for general consumers.",
            PolarityEnum.neutral, 0.83, HorizonEnum.medium_term)

        span_m2 = await _span("q4_2024_earnings",
            "Commercial service with AT&T launched January 15, 2025, ahead of the mid-2025 target.",
            53, 138, "Abel Avellan", "Commercial Update")
        m2 = await _get_or_create_claim(db, company.id, t_commercial.id, span_m2.id,
            span_m2.text,
            "Commercial service launched ahead of schedule on January 15 — execution beat.",
            PolarityEnum.positive, 0.95, HorizonEnum.immediate)

        span_m3 = await _span("q1_2025_earnings",
            "AT&T commercial subscribers reached 180,000.",
            110, 149, "Abel Avellan", "Commercial Update")
        m3 = await _get_or_create_claim(db, company.id, t_commercial.id, span_m3.id,
            span_m3.text,
            "180K AT&T subscribers post-launch — early commercial traction confirmed.",
            PolarityEnum.positive, 0.88, HorizonEnum.immediate)

        all_claims = [c1, c2, c3, c4, c5, t1, t2, t3, k1, k2, k3, k4, r1, r2, r3, m1, m2, m3]
        print(f"  claims: {len(all_claims)}")

        # ── Thread States (17 total) ──────────────────────────────────────────
        # Capital thread: 4 states
        cs1 = await _get_or_create_thread_state(db, t_capital.id, "Q1-2024", -0.30,
            "Cash runway 14 months at $28M/quarter burn. Financing risk moderate.",
            docs["q1_2024_earnings"].id)
        cs2 = await _get_or_create_thread_state(db, t_capital.id, "Q2-2024", 0.20,
            "$200M raise extends runway to 22 months. Burn rising to $34M.",
            docs["q2_2024_earnings"].id)
        cs3 = await _get_or_create_thread_state(db, t_capital.id, "Q4-2024", 0.35,
            "Balance sheet $312M, 20-month runway. Burn $38M. Adequately funded.",
            docs["q4_2024_earnings"].id)
        cs4 = await _get_or_create_thread_state(db, t_capital.id, "Q1-2025", -0.10,
            "Burn $44M/quarter, $268M cash. Additional financing likely needed.",
            docs["q1_2025_earnings"].id)

        # Technical thread: 3 states
        ts1 = await _get_or_create_thread_state(db, t_tech.id, "Q1-2024", 0.55,
            "52 Mbps validated. Early constellation performing at spec.",
            docs["q1_2024_earnings"].id)
        ts2 = await _get_or_create_thread_state(db, t_tech.id, "Q2-2024", 0.70,
            "64 Mbps on Block 2. Technical feasibility no longer in doubt.",
            docs["q2_2024_earnings"].id)
        ts3 = await _get_or_create_thread_state(db, t_tech.id, "Q1-2025", 0.72,
            "58 Mbps avg, 99.2% uptime in commercial ops. Stable performance.",
            docs["q1_2025_earnings"].id)

        # Carrier thread: 4 states
        ks1 = await _get_or_create_thread_state(db, t_carrier.id, "Q1-2024", 0.40,
            "AT&T and Verizon expanded pilots to 35M subscribers.",
            docs["q1_2024_earnings"].id)
        ks2 = await _get_or_create_thread_state(db, t_carrier.id, "Q2-2024", 0.70,
            "AT&T definitive agreement. Verizon in final negotiations. Moat building.",
            docs["q2_2024_earnings"].id)
        ks3 = await _get_or_create_thread_state(db, t_carrier.id, "Q4-2024", 0.80,
            "Verizon signed. Vodafone MOU. Three-carrier moat established.",
            docs["q4_2024_earnings"].id)
        ks4 = await _get_or_create_thread_state(db, t_carrier.id, "Q1-2025", 0.50,
            "AT&T 78% revenue concentration flagged. Moat breadth insufficient.",
            docs["q1_2025_earnings"].id)

        # Regulatory thread: 3 states
        rs1 = await _get_or_create_thread_state(db, t_regulatory.id, "Q2-2024", -0.50,
            "FCC ruling pending. 850 MHz interference risk is primary overhang.",
            docs["q2_2024_earnings"].id)
        rs2 = await _get_or_create_thread_state(db, t_regulatory.id, "Q3-2024", 0.60,
            "FCC conditional waiver received. Regulatory risk materially reduced.",
            docs["q3_2024_8k_fcc"].id)
        rs3 = await _get_or_create_thread_state(db, t_regulatory.id, "Q4-2024", 0.65,
            "Regulatory overhang resolved. Carrier negotiations accelerating.",
            docs["q4_2024_earnings"].id)

        # Commercial thread: 3 states
        ms1 = await _get_or_create_thread_state(db, t_commercial.id, "Q2-2024", 0.30,
            "On track for mid-2025 general consumer launch. Pre-commercial stage.",
            docs["q2_2024_earnings"].id)
        ms2 = await _get_or_create_thread_state(db, t_commercial.id, "Q4-2024", 0.80,
            "AT&T commercial launch January 15, 2025 — ahead of schedule.",
            docs["q4_2024_earnings"].id)
        ms3 = await _get_or_create_thread_state(db, t_commercial.id, "Q1-2025", 0.85,
            "180K AT&T subscribers. Revenue $12.4M. Commercial traction confirmed.",
            docs["q1_2025_earnings"].id)

        all_states = [cs1, cs2, cs3, cs4, ts1, ts2, ts3, ks1, ks2, ks3, ks4, rs1, rs2, rs3, ms1, ms2, ms3]
        print(f"  thread_states: {len(all_states)}")

        # ── State Deltas (8 total) ────────────────────────────────────────────
        sd1 = await _get_or_create_state_delta(db, t_capital.id, c2.id,
            "LiquidityRisk", DeltaDirectionEnum.positive, 0.72, cs2.id)
        sd2 = await _get_or_create_state_delta(db, t_capital.id, c4.id,
            "BurnRate", DeltaDirectionEnum.negative, 0.65, cs4.id)
        sd3 = await _get_or_create_state_delta(db, t_tech.id, t2.id,
            "TechnicalValidation", DeltaDirectionEnum.positive, 0.80, ts2.id)
        sd4 = await _get_or_create_state_delta(db, t_carrier.id, k2.id,
            "CarrierMoat", DeltaDirectionEnum.positive, 0.88, ks2.id)
        sd5 = await _get_or_create_state_delta(db, t_carrier.id, k4.id,
            "CustomerConcentration", DeltaDirectionEnum.negative, 0.70, ks4.id)
        sd6 = await _get_or_create_state_delta(db, t_regulatory.id, r2.id,
            "RegulatoryRisk", DeltaDirectionEnum.positive, 0.92, rs2.id)
        sd7 = await _get_or_create_state_delta(db, t_commercial.id, m2.id,
            "CommercialReadiness", DeltaDirectionEnum.positive, 0.90, ms2.id)
        sd8 = await _get_or_create_state_delta(db, t_commercial.id, m3.id,
            "RevenueVisibility", DeltaDirectionEnum.positive, 0.78, ms3.id)

        all_deltas = [sd1, sd2, sd3, sd4, sd5, sd6, sd7, sd8]
        print(f"  state_deltas: {len(all_deltas)}")

        # ── Transitions (11 total) ────────────────────────────────────────────
        # Capital: Q1→Q2 (raise improves runway)
        tr1 = await _get_or_create_transition(
            db, t_capital.id, cs1.id, cs2.id,
            TransitionMechanismEnum.capital_event, TransitionSpeedEnum.step,
            0.88,
            "$200M convertible note offering extended runway from 14 to 22 months, shifting capital adequacy "
            "from cautious to constructive. Burn rate uptick to $34M offsets some improvement.",
            "Q2-2024", person_id=cfo.id, institution_id=None,
        )
        # Capital: Q2→Q4
        tr2 = await _get_or_create_transition(
            db, t_capital.id, cs2.id, cs3.id,
            TransitionMechanismEnum.earnings_surprise, TransitionSpeedEnum.gradual,
            0.72,
            "Balance sheet strengthened to $312M with 20-month runway. Conservative burn management "
            "supports execution of Block 2 without near-term dilution risk.",
            "Q4-2024", person_id=cfo.id,
        )
        # Capital: Q4→Q1-2025 (burn uptick)
        tr3 = await _get_or_create_transition(
            db, t_capital.id, cs3.id, cs4.id,
            TransitionMechanismEnum.management_guidance, TransitionSpeedEnum.gradual,
            0.75,
            "Burn rate escalation to $44M/quarter reduces runway from 20 to 18 months. "
            "Management flagging need for additional Block 3 financing, introducing dilution risk.",
            "Q1-2025", person_id=cfo.id,
        )
        # Technical: Q1→Q2
        tr4 = await _get_or_create_transition(
            db, t_tech.id, ts1.id, ts2.id,
            TransitionMechanismEnum.technical_milestone, TransitionSpeedEnum.step,
            0.93,
            "Block 2 satellites demonstrated 64 Mbps peak throughput, a 23% improvement over Q1. "
            "Technical feasibility thesis confirmed; risk narrative shifts to execution and constellation scale.",
            "Q2-2024", person_id=ceo.id,
        )
        # Carrier: Q1→Q2
        tr5 = await _get_or_create_transition(
            db, t_carrier.id, ks1.id, ks2.id,
            TransitionMechanismEnum.commercial_agreement, TransitionSpeedEnum.step,
            0.92,
            "AT&T signed definitive commercial agreement. Verizon in final negotiations. "
            "Carrier moat narrative shifts from speculative to partially de-risked.",
            "Q2-2024", person_id=ceo.id, institution_id=att.id,
        )
        # Carrier: Q2→Q4
        tr6 = await _get_or_create_transition(
            db, t_carrier.id, ks2.id, ks3.id,
            TransitionMechanismEnum.commercial_agreement, TransitionSpeedEnum.gradual,
            0.88,
            "Verizon signed and Vodafone MOU adds European dimension. Three-carrier pipeline "
            "establishes asymmetric moat over Starlink direct-to-cell approach.",
            "Q4-2024", person_id=ceo.id, institution_id=verizon.id,
        )
        # Carrier: Q4→Q1-2025 (concentration concern)
        tr7 = await _get_or_create_transition(
            db, t_carrier.id, ks3.id, ks4.id,
            TransitionMechanismEnum.earnings_surprise, TransitionSpeedEnum.reversal,
            0.78,
            "AT&T concentration at 78% of revenue introduces customer concentration risk. "
            "Carrier moat depth questioned until Verizon and Vodafone revenue materializes.",
            "Q1-2025", person_id=cfo.id,
        )
        # Regulatory: Q2→Q3 (FCC waiver)
        tr8 = await _get_or_create_transition(
            db, t_regulatory.id, rs1.id, rs2.id,
            TransitionMechanismEnum.regulatory_change, TransitionSpeedEnum.step,
            0.96,
            "FCC conditional waiver for 850 MHz band removes the primary regulatory overhang. "
            "Spectrum interference risk materially reduced. Carrier negotiations expected to accelerate.",
            "Q3-2024", person_id=ceo.id,
        )
        # Regulatory: Q3→Q4
        tr9 = await _get_or_create_transition(
            db, t_regulatory.id, rs2.id, rs3.id,
            TransitionMechanismEnum.commercial_agreement, TransitionSpeedEnum.gradual,
            0.70,
            "Post-FCC waiver carrier acceleration validates regulatory overhang resolution. "
            "Spectrum risk now residual; focus shifts to commercial execution.",
            "Q4-2024",
        )
        # Commercial: Q2→Q4 (ahead of schedule launch)
        tr10 = await _get_or_create_transition(
            db, t_commercial.id, ms1.id, ms2.id,
            TransitionMechanismEnum.product_launch, TransitionSpeedEnum.step,
            0.94,
            "Commercial service launched January 15, 2025 — six months ahead of mid-2025 guidance. "
            "Execution beat is highly credible catalyst; commercial readiness risk largely retired.",
            "Q4-2024", person_id=ceo.id, institution_id=att.id,
        )
        # Commercial: Q4→Q1-2025 (subscriber traction)
        tr11 = await _get_or_create_transition(
            db, t_commercial.id, ms2.id, ms3.id,
            TransitionMechanismEnum.earnings_surprise, TransitionSpeedEnum.gradual,
            0.85,
            "180K AT&T subscribers and $12.4M revenue in Q1 2025 confirm commercial traction. "
            "Revenue visibility improving; next inflection requires Verizon/Vodafone ramp.",
            "Q1-2025", person_id=ceo.id,
        )

        all_transitions = [tr1, tr2, tr3, tr4, tr5, tr6, tr7, tr8, tr9, tr10, tr11]
        print(f"  transitions: {len(all_transitions)}")

        # ── Market Reactions (5 total) ────────────────────────────────────────
        mr1 = await _get_or_create_market_reaction(
            db, company.id, tr1.id,
            datetime(2024, 8, 14, 16, 30),
            8.4, 3.2, 0.65, False, 1.8, EstimateRevisionEnum.up,
        )
        mr2 = await _get_or_create_market_reaction(
            db, company.id, tr8.id,
            datetime(2024, 11, 5, 9, 45),
            22.7, 8.5, 0.82, True, 2.9, EstimateRevisionEnum.up,
        )
        mr3 = await _get_or_create_market_reaction(
            db, company.id, tr10.id,
            datetime(2025, 2, 28, 16, 0),
            14.2, 4.8, 0.75, True, 2.1, EstimateRevisionEnum.up,
        )
        mr4 = await _get_or_create_market_reaction(
            db, company.id, tr7.id,
            datetime(2025, 5, 9, 16, 30),
            -6.1, 2.3, 0.38, False, 0.8, EstimateRevisionEnum.down,
        )
        mr5 = await _get_or_create_market_reaction(
            db, company.id, tr11.id,
            datetime(2025, 5, 9, 16, 35),
            9.3, 3.7, 0.72, False, 1.6, EstimateRevisionEnum.up,
        )

        all_mr = [mr1, mr2, mr3, mr4, mr5]
        print(f"  market_reactions: {len(all_mr)}")

        await db.commit()
        print("\nSeed complete.")
        print(f"  company_id={company.id}, threads={len(thread_list)}, "
              f"claims={len(all_claims)}, states={len(all_states)}, "
              f"deltas={len(all_deltas)}, transitions={len(all_transitions)}, "
              f"market_reactions={len(all_mr)}")


if __name__ == "__main__":
    asyncio.run(seed())
