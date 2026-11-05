"""The Campus Customs agent team, built with PydanticAI.

Five agents: a Boss that routes and decides, and four specialists it delegates to.

Every agent reaches shop data through the MCP server in `mcp_server/` -- there is no
direct SQL anywhere in this file. Each specialist sees only the MCP tools for its own
domain (see ROLE_TOOLS in models.py), so a specialist cannot quietly do another's job and
skip the handoff.

The Boss delegates by calling its specialists as tools. That is what makes the handoffs
visible in the audit trail instead of hidden inside one model's reasoning.
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPToolset, StdioTransport
from pydantic_ai.tools import ToolDefinition
from pydantic_ai.usage import UsageLimits

import audit
from models import (
    MAX_MODEL_REQUESTS,
    MAX_TOOL_CALLS,
    MAX_TOTAL_TOKENS,
    MCP_SERVER_SCRIPT,
    PROJECT_ROOT,
    PROMPTS_DIR,
    ROLE_TOOLS,
    AgentRole,
    BossPlan,
    SpecialistReport,
    TicketResolution,
    active_model_name,
    build_model,
)

USAGE_LIMITS = UsageLimits(
    request_limit=MAX_MODEL_REQUESTS,
    tool_calls_limit=MAX_TOOL_CALLS,
    total_tokens_limit=MAX_TOTAL_TOKENS,
)

PROMPT_FILES = {
    AgentRole.BOSS: "boss.md",
    AgentRole.INVENTORY: "inventory.md",
    AgentRole.ACCOUNTING: "accounting.md",
    AgentRole.FACILITIES: "facilities.md",
    AgentRole.CUSTOMER_SERVICE: "customer_service.md",
}


class TicketRun:
    """Mutable state for one ticket run: the run id and what the team has done."""

    def __init__(self, ticket_id: int):
        self.ticket_id = ticket_id
        self.run_id = f"t{ticket_id}-{uuid.uuid4().hex[:8]}"
        self.reports: list[SpecialistReport] = []
        self.delegations: list[tuple[AgentRole, str]] = []
        self.tokens: dict[str, int] = {"input": 0, "output": 0, "total": 0}

    def record_usage(self, agent: str, usage: Any) -> dict[str, Any]:
        """Accumulate token spend for this ticket and return the per-agent slice.

        The caps in models.py stop a runaway loop, but they do not tell anyone what a
        run actually cost. Recording usage per agent step is what makes spend visible in
        the audit trail instead of only discoverable on a bill.
        """
        step = {
            "input_tokens": getattr(usage, "input_tokens", 0) or 0,
            "output_tokens": getattr(usage, "output_tokens", 0) or 0,
            "requests": getattr(usage, "requests", 0) or 0,
        }
        step["total_tokens"] = step["input_tokens"] + step["output_tokens"]
        self.tokens["input"] += step["input_tokens"]
        self.tokens["output"] += step["output_tokens"]
        self.tokens["total"] += step["total_tokens"]
        step["ticket_total_so_far"] = self.tokens["total"]
        step["budget_per_agent_run"] = MAX_TOTAL_TOKENS
        step["agent"] = agent
        return step


def load_prompt(role: AgentRole) -> str:
    return (PROMPTS_DIR / PROMPT_FILES[role]).read_text()


def mcp_toolset(role: AgentRole):
    """An MCP connection scoped to the tools this role is allowed to use."""
    allowed = set(ROLE_TOOLS[role])
    toolset = MCPToolset(
        StdioTransport(
            command=str(PROJECT_ROOT / ".venv" / "bin" / "python"),
            args=[str(MCP_SERVER_SCRIPT)],
        ),
        id=f"campus-customs-{role.value}",
    )
    return toolset.filtered(lambda ctx, td: td.name in allowed)


def build_specialist(role: AgentRole) -> Agent[TicketRun, SpecialistReport]:
    return Agent(
        build_model(),
        name=role.value,
        deps_type=TicketRun,
        output_type=SpecialistReport,
        instructions=load_prompt(role),
        toolsets=[mcp_toolset(role)],
    )


# The four specialists.
inventory_agent = build_specialist(AgentRole.INVENTORY)
accounting_agent = build_specialist(AgentRole.ACCOUNTING)
facilities_agent = build_specialist(AgentRole.FACILITIES)
customer_service_agent = build_specialist(AgentRole.CUSTOMER_SERVICE)

SPECIALISTS: dict[AgentRole, Agent[TicketRun, SpecialistReport]] = {
    AgentRole.INVENTORY: inventory_agent,
    AgentRole.ACCOUNTING: accounting_agent,
    AgentRole.FACILITIES: facilities_agent,
    AgentRole.CUSTOMER_SERVICE: customer_service_agent,
}


async def _run_specialist(
    role: AgentRole, run: TicketRun, task: str, why: str
) -> SpecialistReport:
    """Run one specialist and record the delegation and its report in the audit trail."""
    audit.log_event(
        run.run_id, AgentRole.BOSS.value, "delegation", ticket_id=run.ticket_id,
        detail=f"-> {role.value}: {task}", data={"to": role.value, "why": why},
    )
    run.delegations.append((role, task))

    prompt = (
        f"Ticket {run.ticket_id}.\n\nTask from the Boss: {task}\n\n"
        f"Why you were called: {why}\n\n"
        "Use your MCP tools to get the facts before answering."
    )
    result = await SPECIALISTS[role].run(prompt, deps=run, usage_limits=USAGE_LIMITS)
    report = result.output
    report.role = role

    for msg in result.all_messages():
        for part in getattr(msg, "parts", []):
            if part.__class__.__name__ == "ToolCallPart":
                audit.log_event(
                    run.run_id, role.value, "tool_call", ticket_id=run.ticket_id,
                    tool=part.tool_name,
                    data={"args": str(getattr(part, "args", ""))[:400]},
                )
                if part.tool_name not in report.tools_used:
                    report.tools_used.append(part.tool_name)

    audit.log_event(
        run.run_id, role.value, "report", ticket_id=run.ticket_id,
        detail=report.summary,
        data={
            "findings": report.findings,
            "blockers": report.blockers,
            "handoff_to": report.handoff_to.value if report.handoff_to else None,
            "approvals_needed": [a.model_dump(mode="json") for a in report.approvals_needed],
            "tools_used": report.tools_used,
            "usage": run.record_usage(role.value, result.usage),
        },
    )
    run.reports.append(report)
    return report


# ---------------------------------------------------------------------------
# The Boss
# ---------------------------------------------------------------------------

boss_agent = Agent(
    build_model(),
    name=AgentRole.BOSS.value,
    deps_type=TicketRun,
    output_type=TicketResolution,
    instructions=load_prompt(AgentRole.BOSS),
    toolsets=[mcp_toolset(AgentRole.BOSS)],
)


@boss_agent.tool
async def ask_inventory(ctx: RunContext[TicketRun], task: str, why: str) -> dict[str, Any]:
    """Delegate to the Inventory agent: stock by size, shortfalls, restock options."""
    return (await _run_specialist(AgentRole.INVENTORY, ctx.deps, task, why)).model_dump(
        mode="json"
    )


@boss_agent.tool
async def ask_accounting(ctx: RunContext[TicketRun], task: str, why: str) -> dict[str, Any]:
    """Delegate to the Accounting agent: cash, invoices, margins, preparing payments."""
    return (await _run_specialist(AgentRole.ACCOUNTING, ctx.deps, task, why)).model_dump(
        mode="json"
    )


@boss_agent.tool
async def ask_facilities(ctx: RunContext[TicketRun], task: str, why: str) -> dict[str, Any]:
    """Delegate to the Facilities agent: the lease, rent, landlord, shop space."""
    return (await _run_specialist(AgentRole.FACILITIES, ctx.deps, task, why)).model_dump(
        mode="json"
    )


@boss_agent.tool
async def ask_customer_service(
    ctx: RunContext[TicketRun], task: str, why: str
) -> dict[str, Any]:
    """Delegate to the Customer Service agent: draft a reply to the requester."""
    return (
        await _run_specialist(AgentRole.CUSTOMER_SERVICE, ctx.deps, task, why)
    ).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------


async def plan_ticket(ticket_id: int) -> BossPlan:
    """Ask the Boss who it would call, without running anyone. Used for Problem 6."""
    run = TicketRun(ticket_id)
    planner = Agent(
        build_model(),
        name="boss_planner",
        deps_type=TicketRun,
        output_type=BossPlan,
        instructions=load_prompt(AgentRole.BOSS),
        toolsets=[mcp_toolset(AgentRole.BOSS)],
    )
    result = await planner.run(
        f"Plan ticket {ticket_id}. Say who you would call first and why, which "
        "delegations you expect, and which MCP tools you expect to be used. "
        "Do not resolve the ticket.",
        deps=run,
        usage_limits=USAGE_LIMITS,
    )
    plan = result.output
    plan.ticket_id = ticket_id
    audit.log_event(
        run.run_id, AgentRole.BOSS.value, "plan", ticket_id=ticket_id,
        detail=plan.first_call_reason, data=plan.model_dump(mode="json"),
    )
    return plan


async def resolve_ticket(ticket_id: int) -> TicketResolution:
    """Run the full team on one ticket and return the Boss's final call."""
    run = TicketRun(ticket_id)
    audit.log_event(
        run.run_id, AgentRole.BOSS.value, "run_start", ticket_id=ticket_id,
        detail=f"Starting ticket {ticket_id}", data={"model": active_model_name()},
    )

    try:
        result = await boss_agent.run(
            f"Resolve ticket {ticket_id}. Start with get_shop_snapshot, then delegate to "
            "the specialists who are actually needed. Do not call everyone. When they "
            "report back, make the final call.",
            deps=run,
            usage_limits=USAGE_LIMITS,
        )
    except Exception as exc:
        audit.log_event(
            run.run_id, AgentRole.BOSS.value, "error", ticket_id=ticket_id,
            detail=f"{type(exc).__name__}: {exc}",
        )
        raise

    resolution = result.output
    resolution.ticket_id = ticket_id

    # Fill in contributions from the specialists that actually ran, so the record
    # reflects what happened rather than only what the Boss remembered to mention.
    #
    # Approvals are deduplicated on (kind, amount): the Boss and the specialist that
    # raised it both report the same payment, and a human must not see one $840 invoice
    # three times and approve it three times. ref_id is deliberately not part of the key
    # because agents sometimes omit it, which would let the same payment through twice.
    seen: set[tuple[str, float]] = set()
    deduped: list[Any] = []
    for approval in resolution.approvals_requested + [
        a for r in run.reports for a in r.approvals_needed
    ]:
        key = (approval.kind, round(approval.amount, 2))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(approval)
    resolution.approvals_requested = deduped

    for report in run.reports:
        resolution.agent_contributions.setdefault(report.role.value, report.summary)

    audit.log_event(
        run.run_id, AgentRole.BOSS.value, "decision", ticket_id=ticket_id,
        detail=resolution.outcome_summary,
        data={
            **resolution.model_dump(mode="json"),
            "usage": run.record_usage(AgentRole.BOSS.value, result.usage),
            "ticket_token_total": run.tokens,
        },
    )
    return resolution
