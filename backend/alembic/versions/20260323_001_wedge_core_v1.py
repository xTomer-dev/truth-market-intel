"""wedge_core_v1

Revision ID: wedge_core_v1_001
Revises:
Create Date: 2026-03-23

Wedge-core v1 schema: new tables, new columns on existing tables, indexes.
All operations are additive (RULE 6).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

revision = "wedge_core_v1_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # ── Create enum types ──────────────────────────────────────────────────

    person_type_enum = ENUM(
        "executive", "analyst", "board_member", "investor",
        name="person_type_enum", create_type=False,
    )
    person_type_enum.create(bind, checkfirst=True)

    institution_type_enum = ENUM(
        "strategic_partner", "strategic_investor", "sell_side", "buy_side",
        "carrier", "controlling_entity", "insider",
        name="institution_type_enum", create_type=False,
    )
    institution_type_enum.create(bind, checkfirst=True)

    sector_enum = ENUM(
        "technology", "telecommunications", "healthcare", "energy",
        "financials", "industrials", "consumer", "other",
        name="sector_enum", create_type=False,
    )
    sector_enum.create(bind, checkfirst=True)

    document_type_v2_enum = ENUM(
        "10-K", "10-Q", "8-K", "earnings_call", "press_release", "investor_day",
        name="document_type_v2_enum", create_type=False,
    )
    document_type_v2_enum.create(bind, checkfirst=True)

    polarity_v2_enum = ENUM(
        "positive", "negative", "neutral", "cautious",
        name="polarity_v2_enum", create_type=False,
    )
    polarity_v2_enum.create(bind, checkfirst=True)

    horizon_enum = ENUM(
        "immediate", "near_term", "medium_term", "long_term", "unspecified",
        name="horizon_enum", create_type=False,
    )
    horizon_enum.create(bind, checkfirst=True)

    thread_status_enum = ENUM(
        "active", "resolved", "emerging", "stale", "archived",
        name="thread_status_enum", create_type=False,
    )
    thread_status_enum.create(bind, checkfirst=True)

    delta_direction_enum = ENUM(
        "positive", "negative", "neutral",
        name="delta_direction_enum", create_type=False,
    )
    delta_direction_enum.create(bind, checkfirst=True)

    transition_mechanism_enum = ENUM(
        "technical_milestone", "commercial_agreement", "capital_event",
        "regulatory_change", "product_launch", "macro_shift",
        "management_guidance", "earnings_surprise", "other",
        name="transition_mechanism_enum", create_type=False,
    )
    transition_mechanism_enum.create(bind, checkfirst=True)

    transition_speed_enum = ENUM(
        "step", "gradual", "reversal",
        name="transition_speed_enum", create_type=False,
    )
    transition_speed_enum.create(bind, checkfirst=True)

    event_type_v2_enum = ENUM(
        "technical_milestone", "commercial_milestone", "capital_event",
        "regulatory_filing", "earnings_release", "management_change", "other",
        name="event_type_v2_enum", create_type=False,
    )
    event_type_v2_enum.create(bind, checkfirst=True)

    estimate_revision_enum = ENUM(
        "up", "down", "none",
        name="estimate_revision_enum", create_type=False,
    )
    estimate_revision_enum.create(bind, checkfirst=True)

    # ── Create new tables ──────────────────────────────────────────────────

    if not bind.dialect.has_table(bind, "persons"):
        op.create_table(
            "persons",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("type", person_type_enum, nullable=False),
            sa.Column("role", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    if not bind.dialect.has_table(bind, "institutions"):
        op.create_table(
            "institutions",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("type", institution_type_enum, nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    if not bind.dialect.has_table(bind, "evidence_spans"):
        op.create_table(
            "evidence_spans",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("char_offset_start", sa.Integer(), nullable=False),
            sa.Column("char_offset_end", sa.Integer(), nullable=False),
            sa.Column("speaker", sa.String(255), nullable=True),
            sa.Column("section", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_evidence_spans_document_id", "evidence_spans", ["document_id"])

    if not bind.dialect.has_table(bind, "narrative_threads"):
        op.create_table(
            "narrative_threads",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(512), nullable=False),
            sa.Column("description", sa.Text(), server_default="", nullable=False),
            sa.Column("kpi_label", sa.String(255), nullable=True),
            sa.Column("status", thread_status_enum, server_default="active", nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_narrative_threads_company_id", "narrative_threads", ["company_id"])

    if not bind.dialect.has_table(bind, "wedge_events"):
        op.create_table(
            "wedge_events",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(512), nullable=False),
            sa.Column("type", event_type_v2_enum, nullable=False),
            sa.Column("occurred_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_wedge_events_company_id", "wedge_events", ["company_id"])

    if not bind.dialect.has_table(bind, "thread_states"):
        op.create_table(
            "thread_states",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("narrative_thread_id", sa.Uuid(), sa.ForeignKey("narrative_threads.id", ondelete="CASCADE"), nullable=False),
            sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True),
            sa.Column("time_period", sa.String(64), nullable=False),
            sa.Column("sentiment_score", sa.Float(), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("supersedes_thread_state_id", sa.Uuid(), sa.ForeignKey("thread_states.id", ondelete="SET NULL"), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_thread_states_narrative_thread_id", "thread_states", ["narrative_thread_id"])
        op.create_index("ix_thread_states_document_id", "thread_states", ["document_id"])

    if not bind.dialect.has_table(bind, "state_deltas"):
        op.create_table(
            "state_deltas",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("narrative_thread_id", sa.Uuid(), sa.ForeignKey("narrative_threads.id", ondelete="CASCADE"), nullable=False),
            sa.Column("claim_id", sa.Integer(), sa.ForeignKey("claims.id", ondelete="SET NULL"), nullable=True),
            sa.Column("event_id", sa.Uuid(), sa.ForeignKey("wedge_events.id", ondelete="SET NULL"), nullable=True),
            sa.Column("dimension", sa.String(255), nullable=False),
            sa.Column("direction", delta_direction_enum, nullable=False),
            sa.Column("magnitude", sa.Float(), nullable=False),
            sa.Column("modifies_thread_state_id", sa.Uuid(), sa.ForeignKey("thread_states.id", ondelete="SET NULL"), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_state_deltas_narrative_thread_id", "state_deltas", ["narrative_thread_id"])

    if not bind.dialect.has_table(bind, "transitions"):
        op.create_table(
            "transitions",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("narrative_thread_id", sa.Uuid(), sa.ForeignKey("narrative_threads.id", ondelete="CASCADE"), nullable=False),
            sa.Column("from_thread_state_id", sa.Uuid(), sa.ForeignKey("thread_states.id", ondelete="SET NULL"), nullable=True),
            sa.Column("to_thread_state_id", sa.Uuid(), sa.ForeignKey("thread_states.id", ondelete="SET NULL"), nullable=True),
            sa.Column("triggered_by_event_id", sa.Uuid(), sa.ForeignKey("wedge_events.id", ondelete="SET NULL"), nullable=True),
            sa.Column("triggered_by_document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True),
            sa.Column("attributed_to_person_id", sa.Uuid(), sa.ForeignKey("persons.id", ondelete="SET NULL"), nullable=True),
            sa.Column("attributed_to_institution_id", sa.Uuid(), sa.ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True),
            sa.Column("mechanism", transition_mechanism_enum, nullable=False),
            sa.Column("speed", transition_speed_enum, nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("time_period", sa.String(64), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_transitions_narrative_thread_id", "transitions", ["narrative_thread_id"])
        op.create_index("ix_transitions_created_at", "transitions", ["created_at"])

    if not bind.dialect.has_table(bind, "market_reactions"):
        op.create_table(
            "market_reactions",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
            sa.Column("event_id", sa.Uuid(), sa.ForeignKey("wedge_events.id", ondelete="SET NULL"), nullable=True),
            sa.Column("transition_id", sa.Uuid(), sa.ForeignKey("transitions.id", ondelete="SET NULL"), nullable=True),
            sa.Column("reacted_at", sa.DateTime(), nullable=False),
            sa.Column("price_move_pct", sa.Float(), nullable=True),
            sa.Column("volume_vs_avg", sa.Float(), nullable=True),
            sa.Column("sentiment_score", sa.Float(), nullable=True),
            sa.Column("options_iv_spike", sa.Boolean(), nullable=True),
            sa.Column("call_put_ratio", sa.Float(), nullable=True),
            sa.Column("estimate_revision_direction", estimate_revision_enum, nullable=True),
            sa.Column("context", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_market_reactions_company_id", "market_reactions", ["company_id"])
        op.create_index("ix_market_reactions_created_at", "market_reactions", ["created_at"])

    if not bind.dialect.has_table(bind, "document_reports_event"):
        op.create_table(
            "document_reports_event",
            sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("event_id", sa.Uuid(), sa.ForeignKey("wedge_events.id", ondelete="CASCADE"), primary_key=True),
        )

    # ── Add new columns to existing tables ─────────────────────────────────

    # Company additions
    op.add_column("companies", sa.Column("exchange", sa.String(32), nullable=True))
    op.add_column("companies", sa.Column("sector_enum", sector_enum, nullable=True))
    op.add_column("companies", sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True))

    # Document additions
    op.add_column("documents", sa.Column("wc_type", document_type_v2_enum, nullable=True))
    op.add_column("documents", sa.Column("period", sa.String(64), nullable=True))
    op.add_column("documents", sa.Column("raw_text_path", sa.String(1024), nullable=True))
    op.add_column("documents", sa.Column("filed_by_person_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_documents_filed_by_person_id",
        "documents", "persons",
        ["filed_by_person_id"], ["id"],
        ondelete="SET NULL",
    )

    # Claim additions
    op.add_column("claims", sa.Column("evidence_span_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_claims_evidence_span_id",
        "claims", "evidence_spans",
        ["evidence_span_id"], ["id"],
        ondelete="CASCADE",
    )
    op.add_column("claims", sa.Column("narrative_thread_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_claims_narrative_thread_id",
        "claims", "narrative_threads",
        ["narrative_thread_id"], ["id"],
        ondelete="SET NULL",
    )
    op.add_column("claims", sa.Column("made_by_person_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_claims_made_by_person_id",
        "claims", "persons",
        ["made_by_person_id"], ["id"],
        ondelete="SET NULL",
    )
    op.add_column("claims", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("claims", sa.Column("verbatim", sa.Text(), nullable=True))
    op.add_column("claims", sa.Column("wc_polarity", polarity_v2_enum, nullable=True))
    op.add_column("claims", sa.Column("horizon", horizon_enum, nullable=True))
    op.add_column("claims", sa.Column("supersedes_claim_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_claims_supersedes_claim_id",
        "claims", "claims",
        ["supersedes_claim_id"], ["id"],
        ondelete="SET NULL",
    )
    op.add_column("claims", sa.Column("contradicts_claim_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_claims_contradicts_claim_id",
        "claims", "claims",
        ["contradicts_claim_id"], ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Wedge-core v1 is additive only. Downgrade not supported to prevent data loss.
    pass
