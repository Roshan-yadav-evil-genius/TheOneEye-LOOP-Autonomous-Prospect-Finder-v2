from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ValidationResult(BaseModel):
    valid: bool
    missing_sections: list[str]
    completion_pct: int = Field(ge=0, le=100)


class OrganizationCreate(BaseModel):
    name: str = Field(default="Untitled Organization", min_length=1, max_length=255)
    website: HttpUrl | str = Field(default="https://example.com")
    primary_contact_email: str | None = None
    thumbnail_url: str | None = None
    org_form: dict[str, Any] = Field(default_factory=dict)


class OrganizationRead(OrmModel):
    id: str
    name: str
    website: str
    primary_contact_email: str | None
    thumbnail_url: str | None
    org_form: dict[str, Any]
    profile_validated: bool
    products_count: int = 0


class ProfileUpdate(BaseModel):
    """Legacy form-only profile patch (still accepted where identity is unchanged)."""

    form: dict[str, Any]


class OrganizationProfileUpdate(BaseModel):
    form: dict[str, Any]
    name: str | None = Field(default=None, min_length=1, max_length=255)
    website: HttpUrl | None = None
    primary_contact_email: str | None = None
    thumbnail_url: str | None = None


class ProductCreate(BaseModel):
    name: str = Field(default="Untitled Product", min_length=1, max_length=255)
    kind: Literal["product", "service"] = "product"
    thumbnail_url: str | None = None
    icp_form: dict[str, Any] = Field(default_factory=dict)


class ProductProfileUpdate(BaseModel):
    form: dict[str, Any]
    name: str | None = Field(default=None, min_length=1, max_length=255)
    kind: Literal["product", "service"] | None = None
    thumbnail_url: str | None = None


class ProductRead(OrmModel):
    id: str
    organization_id: str
    name: str
    kind: str
    thumbnail_url: str | None
    icp_form: dict[str, Any]
    profile_validated: bool
    strategies_count: int = 0


class SalesStrategyProfileUpdate(BaseModel):
    form: dict[str, Any]
    name: str | None = None


class SalesStrategyCreate(BaseModel):
    sales_strategy_form: dict[str, Any] = Field(default_factory=dict)
    name: str | None = None
    thumbnail_url: str | None = None


class SalesStrategyRead(OrmModel):
    id: str
    product_id: str
    name: str
    thumbnail_url: str | None
    sales_strategy_form: dict[str, Any]
    target_companies: int
    contacts_per_company_default: int
    company_finder_attempt: int
    companies_count: int = 0


class RegisterCompanyRequest(BaseModel):
    name: str = Field(min_length=1)
    website_url: str = Field(min_length=1)
    selection_reason: str = Field(min_length=1)


class RegisterCompanyResult(BaseModel):
    company_id: str
    sales_strategy_company_id: str
    message: Literal["registered", "already_in_db", "already_in_strategy"]


class BlacklistRequest(BaseModel):
    blacklist_reason: str = Field(min_length=1)


class ProspectProfileInput(BaseModel):
    full_name: str = Field(min_length=1)
    job_title: str = Field(min_length=1)
    department: str | None = None
    seniority: str | None = None
    linkedin_url: str
    public_email: str | None = None
    public_phone: str | None = None
    location: str | None = None


class RegisterContactRequest(ProspectProfileInput):
    selection_reason: str = Field(min_length=1)
    fit_rationale: str = Field(min_length=1)
    confidence_score: float = Field(ge=0, le=100)
    evidence_urls: list[str] = Field(default_factory=list)


class BlacklistProspectRequest(BaseModel):
    linkedin_url: str
    blacklist_reason: str = Field(min_length=1)
    full_name: str | None = None
    job_title: str | None = None


class RegistrationResult(BaseModel):
    prospect_profile_id: str
    sales_strategy_prospect_id: str
    message: Literal["registered", "already_in_db", "already_in_strategy", "blacklisted"]


class OutreachUpdate(BaseModel):
    connection_request_status: Literal["sent", "ignored", "accepted"] | None = None
    received_response: bool | None = None
    response_sentiment: Literal["positive", "negative"] | None = None
    response_negative_reason: str | None = None

    @model_validator(mode="after")
    def validate_sentiment(self) -> "OutreachUpdate":
        if self.received_response and not self.response_sentiment:
            raise ValueError("response_sentiment is required when a response was received")
        if self.response_sentiment == "negative" and not self.response_negative_reason:
            raise ValueError("response_negative_reason is required for negative sentiment")
        return self


class ProspectRead(OrmModel):
    id: str
    prospect_profile_id: str
    full_name: str | None
    job_title: str | None
    linkedin_url: str
    selection_reason: str
    fit_rationale: str
    confidence_score: float | None
    is_blacklisted: bool
    blacklist_reason: str | None
    connection_request_status: str | None
    received_response: bool | None
    response_sentiment: str | None
    response_negative_reason: str | None
    discovery_thread_id: str | None


class CompanySummary(OrmModel):
    id: str
    company_id: str
    name: str
    domain: str
    selection_reason: str
    funnel_stage: str
    prospect_queue_status: str | None
    contacts_target: int
    contacts_registered: int
    is_blacklisted: bool
    blacklist_reason: str | None
    discovery_thread_id: str | None


class CompanyDetail(BaseModel):
    company: CompanySummary
    profile: dict[str, Any] | None
    prospects: list[ProspectRead]


class CompanyProfileUpdate(BaseModel):
    profile: dict[str, Any]


class FormMarkdownTemplate(BaseModel):
    filename: str
    content: str


class ProgressRead(BaseModel):
    companies_registered: int
    target_companies: int
    companies_validated: int
    contacts_registered: int
    contacts_target: int


AgentRole = Literal["company-finder", "contact-finder"]


class ProcessLogRead(OrmModel):
    id: str
    level: str
    event_code: str
    message: str
    trace_id: str | None
    created_at: datetime


class ProcessStatus(BaseModel):
    role: AgentRole
    desired_state: str
    actual_state: str
    active_company_id: str | None
    last_error: str | None
    execution_count: int
    logs: list[ProcessLogRead]




class AgentRunSummary(OrmModel):
    id: str
    agent_role: str
    effort_prefix: str
    primary_thread_id: str
    company_id: str | None
    sales_strategy_prospect_id: str | None
    status: str
    attempt_iteration: int
    contact_attempt_iteration: int | None
    child_thread_ids: list[str]
    created_at: datetime


class EffortDetailRead(OrmModel):
    id: str
    sales_strategy_id: str
    product_id: str
    agent_role: str
    effort_prefix: str
    primary_thread_id: str
    company_id: str | None = None
    sales_strategy_prospect_id: str | None = None
    status: str
    attempt_iteration: int
    contact_attempt_iteration: int | None = None
    child_thread_ids: list[str] = Field(default_factory=list)
    active_subagent_threads: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    completed_at: datetime | None = None



class ThreadSnapshot(BaseModel):
    thread_id: str
    effort_prefix: str
    available_threads: list[str]
    state: dict[str, Any] | None
    checkpoint_backend: Literal["postgresql", "unavailable"]


class SalesStrategyBundle(BaseModel):
    organization: OrganizationRead
    product: ProductRead
    sales_strategy: SalesStrategyRead


class ScheduledTaskCreate(BaseModel):
    key: str = Field(min_length=1)
    interval_seconds: int = Field(ge=60, le=86400)
    enabled: bool = True
    overlap_policy: Literal["skip", "queue"] = "skip"
    payload: dict[str, Any] = Field(default_factory=dict)


class ScheduledTaskRead(OrmModel):
    id: str
    key: str
    interval_seconds: int
    enabled: bool
    overlap_policy: str
    payload: dict[str, Any]
    next_run_at: datetime


class JobRunRead(OrmModel):
    id: str
    task_key: str
    status: str
    attempts: int
    payload: dict[str, Any]
    error: str | None
    created_at: datetime


class DeadLetterRead(OrmModel):
    id: str
    queue: str
    job_run_id: str
    reason: str
    attempts: int
    replay_state: str
    payload: dict[str, Any]
    created_at: datetime


class IntegrationEventRead(OrmModel):
    id: str
    event_type: str
    version: int
    payload: dict[str, Any]
    correlation_id: str | None
    published_at: datetime | None
    attempts: int
    created_at: datetime


class AuditEventRead(OrmModel):
    id: str
    actor: str
    action: str
    entity_type: str
    entity_id: str
    before: dict[str, Any]
    after: dict[str, Any]
    reason: str | None
    request_id: str | None
    created_at: datetime


class BrainMemoryCreate(BaseModel):
    agent_type: str
    category: Literal["actions", "failures", "decisions", "insights"]
    content: str = Field(min_length=1)
    evidence_urls: list[str] = Field(default_factory=list)


class BrainMemoryRead(OrmModel):
    id: str
    sales_strategy_id: str
    agent_type: str
    category: str
    content: str
    evidence_urls: list[str]
    created_at: datetime


class ChatStreamRequest(BaseModel):
    message: str = Field(default="", min_length=0)
    mode: Literal["chat", "agent"]
    retry: bool = False
    redo_last: bool = False
    thread_id: str | None = None
    is_planner: bool = False



class ChatHistoryRead(BaseModel):
    thread_id: str
    messages: list[dict[str, Any]]
    can_resume: bool = False


class StateSnapshotRead(BaseModel):
    step_index: int
    checkpoint_id: str | None = None
    checkpoint_ns: str | None = None
    parent_checkpoint_id: str | None = None
    values: dict[str, Any]
    next: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)



class NewThreadResponse(BaseModel):
    thread_id: str



class ToolCustomizationRuleCreate(BaseModel):
    tool_name_prefix: str = Field(min_length=1, max_length=255)
    icon_url: str | None = Field(default=None, max_length=2048)
    request_color: str | None = None
    response_color: str | None = None


class ToolCustomizationRuleRead(OrmModel):
    id: str
    tool_name_prefix: str
    icon_url: str | None
    request_color: str | None
    response_color: str | None
