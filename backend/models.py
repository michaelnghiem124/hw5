"""Shared data types and model configuration for the Campus Customs agent team.

Everything the agents pass between each other is defined here so the shapes stay
consistent across the agent layer, the audit trail, and the API.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from dotenv import dotenv_values
from pydantic import BaseModel, Field

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
PROMPTS_DIR = BACKEND_DIR / "prompts"
DB_PATH = PROJECT_ROOT / "data" / "campus_customs_new.db"
ORIGINAL_DB_PATH = PROJECT_ROOT / "data" / "campus_customs.db"
AUDIT_PATH = PROJECT_ROOT / "output" / "audit_trail.json"
MCP_SERVER_SCRIPT = PROJECT_ROOT / "mcp_server" / "server.py"

# Shared out-of-iCloud env first, then a local .env, never overriding a variable
# that is already set in the environment. Same pattern as the other MGT 409 projects.
# Values are applied explicitly rather than via load_dotenv, which parses these files
# correctly but does not reliably populate os.environ in this setup.
for _env_file in (Path.home() / ".config" / "mgt409" / ".env", PROJECT_ROOT / ".env"):
    if _env_file.is_file():
        for _key, _value in dotenv_values(_env_file).items():
            if _value is not None and not os.environ.get(_key):
                os.environ[_key] = _value


# ---------------------------------------------------------------------------
# Model provider
# ---------------------------------------------------------------------------
#
# The assignment specifies gpt-6-luna through a Portkey gateway. That is the
# default whenever PORTKEY_API_KEY is present. When it is not -- which is the case
# on this machine -- the team falls back to Anthropic so the system is runnable and
# testable. Switching is an env change, not a code change.

PORTKEY_MODEL = os.environ.get("PORTKEY_MODEL", "gpt-6-luna")
PORTKEY_BASE_URL = os.environ.get("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")


def resolve_provider() -> Literal["portkey", "anthropic"]:
    """Pick the provider from the environment. Explicit setting wins, else key presence."""
    explicit = os.environ.get("MODEL_PROVIDER", "").strip().lower()
    if explicit in ("portkey", "anthropic"):
        return explicit  # type: ignore[return-value]
    return "portkey" if os.environ.get("PORTKEY_API_KEY") else "anthropic"


def build_model():
    """Return a configured PydanticAI model for the active provider."""
    provider = resolve_provider()

    if provider == "portkey":
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider

        key = os.environ.get("PORTKEY_API_KEY")
        if not key:
            raise RuntimeError(
                "MODEL_PROVIDER=portkey but PORTKEY_API_KEY is not set. "
                "Set the key or switch MODEL_PROVIDER=anthropic."
            )
        return OpenAIChatModel(
            PORTKEY_MODEL,
            provider=OpenAIProvider(api_key=key, base_url=PORTKEY_BASE_URL),
        )

    from pydantic_ai.models.anthropic import AnthropicModel

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Add it to ~/.config/mgt409/.env or a local .env."
        )
    return AnthropicModel(ANTHROPIC_MODEL)


def active_model_name() -> str:
    return PORTKEY_MODEL if resolve_provider() == "portkey" else ANTHROPIC_MODEL


# ---------------------------------------------------------------------------
# Safety limits
# ---------------------------------------------------------------------------
# Soft caps let an agent wrap up gracefully; PydanticAI's UsageLimits are the hard
# backstop that ends a runaway loop. Both exist because a loop that never stops is
# the most expensive failure mode a team like this has.

MAX_MODEL_REQUESTS = 12        # per specialist run
MAX_TOOL_CALLS = 10            # per specialist run
MAX_TOTAL_TOKENS = 120_000     # per specialist run
MAX_DELEGATIONS_PER_TICKET = 4  # the Boss may not call everyone for everything


class AgentRole(str, Enum):
    BOSS = "boss"
    INVENTORY = "inventory"
    ACCOUNTING = "accounting"
    FACILITIES = "facilities"
    CUSTOMER_SERVICE = "customer_service"


# Which MCP tools each specialist is allowed to touch. The Boss gets wide read
# access because its job is routing; specialists are scoped to their own domain so
# they cannot quietly do each other's work and skip the handoff.
ROLE_TOOLS: dict[AgentRole, list[str]] = {
    AgentRole.BOSS: [
        "get_shop_snapshot", "get_team_workload", "list_tickets", "get_ticket_context",
    ],
    AgentRole.INVENTORY: [
        "lookup_inventory", "get_inventory_pressure", "check_product_availability",
        "list_vendors",
    ],
    AgentRole.ACCOUNTING: [
        "get_cash_position", "get_financial_overview", "quote_bulk_order",
        "check_rent_obligation",
    ],
    AgentRole.FACILITIES: [
        "get_facilities_obligations", "check_rent_obligation", "list_vendors",
    ],
    AgentRole.CUSTOMER_SERVICE: [
        "list_tickets", "get_ticket_context", "check_product_availability",
    ],
}


# ---------------------------------------------------------------------------
# What agents hand back
# ---------------------------------------------------------------------------


class ApprovalRequest(BaseModel):
    """A payment or purchase an agent has prepared. Never executed by an agent.

    Agents may only propose. The money moves when a human clicks approve and the
    backend writes to `payments` and `cash_accounts`.
    """

    kind: Literal["invoice_payment", "rent_payment", "purchase_order"]
    amount: float
    description: str
    reason: str = Field(description="Why this spend is necessary, in plain language.")
    ref_id: int | None = Field(
        default=None, description="Invoice id or lease id this refers to."
    )
    vendor_id: int | None = None
    account: str = "checking"
    balance_before: float | None = None
    balance_after: float | None = None
    requested_by: AgentRole = AgentRole.ACCOUNTING
    status: Literal["pending_human_approval", "approved", "rejected"] = (
        "pending_human_approval"
    )


class ApproveRequest(BaseModel):
    """A human clicking approve on one prepared payment.

    `amount` is a claim, not an instruction: the API checks it against `invoices.amount`
    or `leases.monthly_rent` before any money moves. `gt=0` enforces the shop rule that
    cash only ever goes out -- a negative amount would be a deposit.
    """

    kind: Literal["invoice_payment", "rent_payment", "purchase_order"]
    amount: float = Field(gt=0)
    approved_by: str = Field(min_length=1, description="The human taking responsibility.")
    ref_id: int | None = Field(
        default=None, description="Invoice id or lease id. Recovered from amount if omitted."
    )
    account: str = "checking"
    note: str | None = None


class ResetRequest(BaseModel):
    """Explicit confirmation for a destructive reset.

    Required so a stray browser refresh or link prefetch cannot wipe a finished run.
    """

    confirm: bool = False


class SpecialistReport(BaseModel):
    """What one specialist found and recommends."""

    role: AgentRole
    summary: str = Field(description="What this agent found, in two or three sentences.")
    findings: list[str] = Field(
        default_factory=list,
        description="Specific facts with real numbers pulled from MCP tools.",
    )
    blockers: list[str] = Field(
        default_factory=list, description="Anything preventing resolution."
    )
    recommended_actions: list[str] = Field(default_factory=list)
    approvals_needed: list[ApprovalRequest] = Field(default_factory=list)
    handoff_to: AgentRole | None = Field(
        default=None,
        description="Another specialist who must act next, if the work is not done.",
    )
    handoff_reason: str | None = None
    draft_message: str | None = Field(
        default=None, description="Customer-facing text. Drafts only, never sent."
    )
    tools_used: list[str] = Field(default_factory=list)


class Delegation(BaseModel):
    """The Boss's decision to hand a ticket to a specialist."""

    to: AgentRole
    task: str = Field(description="What that specialist should do, specifically.")
    why: str = Field(description="Why this specialist and not another.")


class BossPlan(BaseModel):
    """The Boss's routing decision for one ticket."""

    ticket_id: int
    first_call: AgentRole = Field(description="Who to call first.")
    first_call_reason: str
    delegations: list[Delegation] = Field(
        default_factory=list, max_length=MAX_DELEGATIONS_PER_TICKET
    )
    expected_tools: list[str] = Field(default_factory=list)


class TicketResolution(BaseModel):
    """The Boss's final call on a ticket, after the specialists report back."""

    ticket_id: int
    status: Literal["resolved", "blocked", "awaiting_approval"]
    outcome_summary: str
    agent_contributions: dict[str, str] = Field(
        default_factory=dict, description="role -> what that agent contributed."
    )
    approvals_requested: list[ApprovalRequest] = Field(default_factory=list)
    customer_message: str | None = None
    cash_impact: float = Field(
        default=0.0, description="Cash leaving the shop for this ticket, as a positive number."
    )


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


class AuditEvent(BaseModel):
    """One step of the agent loop, appended to output/audit_trail.json."""

    run_id: str
    ticket_id: int | None = None
    agent: str
    event: str = Field(description="delegation | tool_call | report | decision | refusal")
    tool: str | None = None
    detail: str | None = None
    data: dict[str, Any] | None = None
    model: str = Field(default_factory=active_model_name)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
