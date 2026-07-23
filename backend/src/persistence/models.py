from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    inspect,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from persistence.database import Base


def new_id() -> str:
    return str(uuid4())


def now() -> datetime:
    return datetime.now(UTC)


class Timestamped:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class Organization(Timestamped, Base):
    __tablename__ = "organization"
    name: Mapped[str] = mapped_column(String(255))
    website: Mapped[str] = mapped_column(String(2048))
    primary_contact_email: Mapped[str | None] = mapped_column(String(320))
    thumbnail_url: Mapped[str | None] = mapped_column(String(2048))
    org_form: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    profile_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    products: Mapped[list["Product"]] = relationship("Product", backref="organization", lazy="selectin", cascade="all, delete-orphan")

    @property
    def products_count(self) -> int:
        state = inspect(self)
        if state is None or "products" in state.unloaded:
            return 0
        return len(self.products) if self.products is not None else 0


class Product(Timestamped, Base):
    __tablename__ = "product"
    organization_id: Mapped[str] = mapped_column(ForeignKey("organization.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(20))
    thumbnail_url: Mapped[str | None] = mapped_column(String(2048))
    icp_form: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    profile_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    sales_strategies: Mapped[list["SalesStrategy"]] = relationship("SalesStrategy", backref="product", lazy="selectin", cascade="all, delete-orphan")
    __table_args__ = (CheckConstraint("kind IN ('product','service')"),)

    @property
    def strategies_count(self) -> int:
        state = inspect(self)
        if state is None or "sales_strategies" in state.unloaded:
            return 0
        return len(self.sales_strategies) if self.sales_strategies is not None else 0


class SalesStrategy(Timestamped, Base):
    __tablename__ = "sales_strategy"
    product_id: Mapped[str] = mapped_column(ForeignKey("product.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    thumbnail_url: Mapped[str | None] = mapped_column(String(2048))
    sales_strategy_form: Mapped[dict[str, Any]] = mapped_column(JSON)
    target_companies: Mapped[int] = mapped_column(Integer)
    contacts_per_company_default: Mapped[int] = mapped_column(Integer)
    company_finder_attempt: Mapped[int] = mapped_column(Integer, default=0)
    company_effort_seq: Mapped[int] = mapped_column(Integer, default=0)
    companies: Mapped[list["SalesStrategyCompany"]] = relationship("SalesStrategyCompany", backref="sales_strategy", lazy="selectin", cascade="all, delete-orphan")
    __table_args__ = (
        CheckConstraint("target_companies > 0"),
        CheckConstraint("contacts_per_company_default >= 0"),
    )

    @property
    def companies_count(self) -> int:
        state = inspect(self)
        if state is None or "companies" in state.unloaded:
            return 0
        return len(self.companies) if self.companies is not None else 0


class Company(Timestamped, Base):
    __tablename__ = "company"
    name: Mapped[str] = mapped_column(String(255))
    domain: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    profile: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class ProspectProfile(Timestamped, Base):
    __tablename__ = "prospect_profile"
    full_name: Mapped[str | None] = mapped_column(String(255))
    job_title: Mapped[str | None] = mapped_column(String(255))
    department: Mapped[str | None] = mapped_column(String(255))
    seniority: Mapped[str | None] = mapped_column(String(100))
    linkedin_url: Mapped[str] = mapped_column(String(2048), unique=True, index=True)
    public_email: Mapped[str | None] = mapped_column(String(320))
    public_phone: Mapped[str | None] = mapped_column(String(100))
    location: Mapped[str | None] = mapped_column(String(255))


class CompanyProspect(Timestamped, Base):
    __tablename__ = "company_prospect"
    company_id: Mapped[str] = mapped_column(ForeignKey("company.id", ondelete="CASCADE"))
    prospect_profile_id: Mapped[str] = mapped_column(
        ForeignKey("prospect_profile.id", ondelete="CASCADE"), unique=True
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class SalesStrategyCompany(Timestamped, Base):
    __tablename__ = "sales_strategy_company"
    sales_strategy_id: Mapped[str] = mapped_column(
        ForeignKey("sales_strategy.id", ondelete="CASCADE")
    )
    company_id: Mapped[str] = mapped_column(ForeignKey("company.id", ondelete="CASCADE"))
    selection_reason: Mapped[str] = mapped_column(Text)
    funnel_stage: Mapped[str] = mapped_column(String(40), default="registered")
    prospect_queue_status: Mapped[str | None] = mapped_column(String(40))
    contacts_target: Mapped[int] = mapped_column(Integer, default=0)
    sales_strategy_attempt_at_register: Mapped[int] = mapped_column(Integer)
    contact_finder_attempt: Mapped[int] = mapped_column(Integer, default=0)
    contact_effort_seq: Mapped[int] = mapped_column(Integer, default=0)
    discovery_thread_id: Mapped[str | None] = mapped_column(String(512))
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_blacklisted: Mapped[bool] = mapped_column(Boolean, default=False)
    blacklist_reason: Mapped[str | None] = mapped_column(Text)
    blacklisted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    blacklisted_by: Mapped[str | None] = mapped_column(String(20))
    __table_args__ = (
        UniqueConstraint("sales_strategy_id", "company_id"),
        CheckConstraint("is_blacklisted = 0 OR blacklist_reason IS NOT NULL"),
    )


class SalesStrategyProspect(Timestamped, Base):
    __tablename__ = "sales_strategy_prospect"
    sales_strategy_id: Mapped[str] = mapped_column(
        ForeignKey("sales_strategy.id", ondelete="CASCADE")
    )
    company_id: Mapped[str] = mapped_column(ForeignKey("company.id", ondelete="CASCADE"))
    prospect_profile_id: Mapped[str] = mapped_column(
        ForeignKey("prospect_profile.id", ondelete="CASCADE")
    )
    selection_reason: Mapped[str] = mapped_column(Text, default="")
    fit_rationale: Mapped[str] = mapped_column(Text, default="")
    confidence_score: Mapped[float | None] = mapped_column(Float)
    evidence_urls: Mapped[list[str]] = mapped_column(JSON, default=list)
    discovery_thread_id: Mapped[str | None] = mapped_column(String(512))
    is_blacklisted: Mapped[bool] = mapped_column(Boolean, default=False)
    blacklist_reason: Mapped[str | None] = mapped_column(Text)
    blacklisted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    blacklisted_by: Mapped[str | None] = mapped_column(String(20))
    connection_request_status: Mapped[str | None] = mapped_column(String(20))
    received_response: Mapped[bool | None] = mapped_column(Boolean)
    response_sentiment: Mapped[str | None] = mapped_column(String(20))
    response_negative_reason: Mapped[str | None] = mapped_column(Text)
    outreach_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("sales_strategy_id", "company_id", "prospect_profile_id"),
        CheckConstraint("is_blacklisted = 0 OR blacklist_reason IS NOT NULL"),
    )


class AgentProcessState(Timestamped, Base):
    __tablename__ = "agent_process_state"
    sales_strategy_id: Mapped[str] = mapped_column(
        ForeignKey("sales_strategy.id", ondelete="CASCADE")
    )
    role: Mapped[str] = mapped_column(String(30))
    desired_state: Mapped[str] = mapped_column(String(20), default="stopped")
    actual_state: Mapped[str] = mapped_column(String(20), default="stopped")
    active_company_id: Mapped[str | None] = mapped_column(String(36))
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("sales_strategy_id", "role"),)


class AgentSubagentState(Timestamped, Base):
    """Durable nested child-thread map for a parent orchestrator role thread."""

    __tablename__ = "agent_subagent_state"
    parent_thread_id: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    active_subagent_threads: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class AgentRun(Timestamped, Base):
    __tablename__ = "agent_run"
    product_id: Mapped[str] = mapped_column(ForeignKey("product.id"))
    sales_strategy_id: Mapped[str] = mapped_column(ForeignKey("sales_strategy.id"))
    company_id: Mapped[str | None] = mapped_column(ForeignKey("company.id"))
    sales_strategy_prospect_id: Mapped[str | None] = mapped_column(
        ForeignKey("sales_strategy_prospect.id")
    )
    agent_role: Mapped[str] = mapped_column(String(30))
    effort_prefix: Mapped[str] = mapped_column(String(512), unique=True)
    primary_thread_id: Mapped[str] = mapped_column(String(512))
    attempt_iteration: Mapped[int] = mapped_column(Integer)
    contact_attempt_iteration: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="running")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0)
    child_thread_ids: Mapped[list[str]] = mapped_column(JSON, default=list)


class Whiteboard(Timestamped, Base):
    __tablename__ = "whiteboard"
    sales_strategy_id: Mapped[str] = mapped_column(
        ForeignKey("sales_strategy.id", ondelete="CASCADE")
    )
    role: Mapped[str] = mapped_column(String(30))
    effort_prefix: Mapped[str | None] = mapped_column(String(512))
    content: Mapped[str] = mapped_column(Text, default="")
    __table_args__ = (UniqueConstraint("sales_strategy_id", "role"),)


class ProcessLog(Timestamped, Base):
    __tablename__ = "process_log"
    sales_strategy_id: Mapped[str] = mapped_column(
        ForeignKey("sales_strategy.id", ondelete="CASCADE")
    )
    role: Mapped[str] = mapped_column(String(30))
    level: Mapped[str] = mapped_column(String(20), default="info")
    event_code: Mapped[str] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(Text)
    trace_id: Mapped[str | None] = mapped_column(String(128))


class AuditEvent(Timestamped, Base):
    __tablename__ = "audit_event"
    actor: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[str] = mapped_column(String(36))
    before: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    after: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    reason: Mapped[str | None] = mapped_column(Text)
    request_id: Mapped[str | None] = mapped_column(String(128))


class IntegrationEvent(Timestamped, Base):
    __tablename__ = "integration_event"
    event_type: Mapped[str] = mapped_column(String(150), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    producer: Mapped[str] = mapped_column(String(100), default="loop-api")
    correlation_id: Mapped[str | None] = mapped_column(String(128))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    last_error: Mapped[str | None] = mapped_column(Text)
    dead_lettered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ConsumerInbox(Timestamped, Base):
    __tablename__ = "consumer_inbox"
    consumer: Mapped[str] = mapped_column(String(100))
    event_id: Mapped[str] = mapped_column(String(36))
    status: Mapped[str] = mapped_column(String(20), default="processed")
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (UniqueConstraint("consumer", "event_id"),)


class ScheduledTask(Timestamped, Base):
    __tablename__ = "scheduled_task"
    key: Mapped[str] = mapped_column(String(100), unique=True)
    interval_seconds: Mapped[int] = mapped_column(Integer)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    overlap_policy: Mapped[str] = mapped_column(String(10), default="skip")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class JobRun(Timestamped, Base):
    __tablename__ = "job_run"
    task_key: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    trace_id: Mapped[str | None] = mapped_column(String(128))


class DeadLetter(Timestamped, Base):
    __tablename__ = "dead_letter"
    queue: Mapped[str] = mapped_column(String(100))
    job_run_id: Mapped[str] = mapped_column(String(36))
    reason: Mapped[str] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer)
    replay_state: Mapped[str] = mapped_column(String(20), default="pending")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class BrainMemory(Timestamped, Base):
    __tablename__ = "brain_memory"
    sales_strategy_id: Mapped[str] = mapped_column(
        ForeignKey("sales_strategy.id", ondelete="CASCADE"), index=True
    )
    agent_type: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(30))
    content: Mapped[str] = mapped_column(Text)
    terms: Mapped[list[str]] = mapped_column(JSON, default=list)
    embedding: Mapped[list[float]] = mapped_column(JSON, default=list)
    evidence_urls: Mapped[list[str]] = mapped_column(JSON, default=list)


class BrowserSession(Timestamped, Base):
    __tablename__ = "browser_session"
    profile_id: Mapped[str] = mapped_column(String(100), unique=True)
    state: Mapped[str] = mapped_column(String(20), default="available")
    lease_owner: Mapped[str | None] = mapped_column(String(512))
    leased_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    health: Mapped[str] = mapped_column(String(20), default="unknown")


class ToolCustomizationRule(Timestamped, Base):
    __tablename__ = "tool_customization_rule"
    tool_name_prefix: Mapped[str] = mapped_column(String(255), unique=True)
    icon_url: Mapped[str | None] = mapped_column(String(2048))
    request_color: Mapped[str | None] = mapped_column(String(20))
    response_color: Mapped[str | None] = mapped_column(String(20))
