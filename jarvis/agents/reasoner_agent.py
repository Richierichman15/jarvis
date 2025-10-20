#!/usr/bin/env python3
"""
ReasonerAgent - Local reasoning and reflection layer for Jarvis

This agent takes tool results from other agents, reflects on them, and produces
concise, actionable guidance before responding back to the user or orchestrator.

Primary responsibilities:
- Summarize multi-tool outputs with pros/cons and confidence
- Reflect on recent actions and propose next steps
- Adjust recommendations based on simple risk heuristics

It prefers a local model via ModelManager when available, and falls back to
deterministic rule-based reasoning otherwise.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from .agent_base import AgentBase, AgentCapability, TaskRequest, TaskResponse
except ImportError:
    # Handle direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from jarvis.agents.agent_base import AgentBase, AgentCapability, TaskRequest, TaskResponse

try:
    from jarvis.models.model_manager import ModelManager
    MODEL_MANAGER_AVAILABLE = True
except Exception:
    MODEL_MANAGER_AVAILABLE = False


logger = logging.getLogger(__name__)


class ReasonerAgent(AgentBase):
    """Agent that performs reflection over tool outputs and context."""

    def __init__(self, **kwargs):
        super().__init__(
            name="ReasonerAgent",
            capabilities=[AgentCapability.SYSTEM],
            version="1.0.0",
            **kwargs
        )

        self.personality = (
            "analytical, concise, risk-aware, with practical suggestions"
        )
        self.model_manager: Optional[ModelManager] = None

    async def start(self, redis_comm=None, agent_manager=None):
        await super().start(redis_comm, agent_manager)

    def _register_task_handlers(self):
        self.register_task_handler("reflect", self._handle_reflect)
        self.register_task_handler("critique", self._handle_critique)
        self.register_task_handler("plan_next_actions", self._handle_plan_next_actions)

    async def _initialize(self):
        try:
            if MODEL_MANAGER_AVAILABLE:
                try:
                    self.model_manager = ModelManager()
                    self.logger.info("✅ ModelManager initialized for ReasonerAgent")
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not initialize ModelManager: {e}")
                    self.model_manager = None
        except Exception as e:
            self.logger.error(f"Failed during ReasonerAgent initialization: {e}")
            raise

    async def _cleanup(self):
        # Nothing persistent to clean yet
        return

    async def _handle_task(self, task: TaskRequest) -> TaskResponse:
        try:
            handler = self.task_handlers.get(task.task_type)
            if handler:
                return await handler(task)
            raise ValueError(f"Unknown reasoner task type: {task.task_type}")
        except Exception as e:
            self.logger.error(f"Error handling reasoner task {task.task_type}: {e}")
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )

    # -----------------------------
    # Task Handlers
    # -----------------------------

    async def _handle_reflect(self, task: TaskRequest) -> TaskResponse:
        """Reflect over tool results and produce a concise assessment.

        Expected parameters:
        - results: List[Dict|str] tool outputs
        - context: Dict optional system/user context
        - domain: str e.g., "trading", "research", "planning"
        """
        results = task.parameters.get("results", [])
        context = task.parameters.get("context", {})
        domain = task.parameters.get("domain", "general")

        text_blob = _compact_results(results)
        prompt = _build_reflection_prompt(text_blob, context, domain, self.personality)

        if self.model_manager:
            try:
                reflection = await self.model_manager.generate(
                    prompt,
                    temperature=0.2,
                    max_tokens=600,
                )
            except Exception as e:
                self.logger.warning(f"LLM reflection failed, using fallback: {e}")
                reflection = _rule_based_reflection(results, context, domain)
        else:
            reflection = _rule_based_reflection(results, context, domain)

        return TaskResponse(
            task_id=task.task_id,
            agent_id=self.agent_id,
            success=True,
            result={
                "reflection": reflection,
                "generated_at": datetime.now().isoformat(),
            },
        )

    async def _handle_critique(self, task: TaskRequest) -> TaskResponse:
        """Provide risks, uncertainties, and opposing viewpoints."""
        results = task.parameters.get("results", [])
        context = task.parameters.get("context", {})
        domain = task.parameters.get("domain", "general")

        text_blob = _compact_results(results)
        prompt = _build_critique_prompt(text_blob, context, domain, self.personality)

        if self.model_manager:
            try:
                critique = await self.model_manager.generate(
                    prompt,
                    temperature=0.2,
                    max_tokens=400,
                )
            except Exception as e:
                self.logger.warning(f"LLM critique failed, using fallback: {e}")
                critique = _rule_based_critique(results, context, domain)
        else:
            critique = _rule_based_critique(results, context, domain)

        return TaskResponse(
            task_id=task.task_id,
            agent_id=self.agent_id,
            success=True,
            result={
                "critique": critique,
                "generated_at": datetime.now().isoformat(),
            },
        )

    async def _handle_plan_next_actions(self, task: TaskRequest) -> TaskResponse:
        """Suggest next actions as a short ordered list."""
        results = task.parameters.get("results", [])
        context = task.parameters.get("context", {})
        domain = task.parameters.get("domain", "general")

        text_blob = _compact_results(results)
        prompt = _build_plan_prompt(text_blob, context, domain, self.personality)

        if self.model_manager:
            try:
                plan = await self.model_manager.generate(
                    prompt,
                    temperature=0.2,
                    max_tokens=300,
                )
            except Exception as e:
                self.logger.warning(f"LLM planning failed, using fallback: {e}")
                plan = _rule_based_plan(results, context, domain)
        else:
            plan = _rule_based_plan(results, context, domain)

        return TaskResponse(
            task_id=task.task_id,
            agent_id=self.agent_id,
            success=True,
            result={
                "plan": plan,
                "generated_at": datetime.now().isoformat(),
            },
        )


# -----------------------------
# Helpers
# -----------------------------

def _compact_results(results: List[Any]) -> str:
    if not results:
        return "(no results)"
    try:
        return json.dumps(results, indent=2, ensure_ascii=False)[:8000]
    except Exception:
        return str(results)[:8000]


def _build_reflection_prompt(text: str, context: Dict[str, Any], domain: str, personality: str) -> str:
    return (
        "You are a reflection layer for Jarvis. Personality: "
        + personality
        + "\nDomain: "
        + domain
        + "\nContext: "
        + json.dumps(context, ensure_ascii=False)
        + "\nSummarize key insights from the tool results, with: "
          "- brief summary\n- pros/cons\n- confidence (0-1)\n- 2-3 actionable suggestions.\n\n"
        + "Tool Results:\n"
        + text
    )


def _build_critique_prompt(text: str, context: Dict[str, Any], domain: str, personality: str) -> str:
    return (
        "You are Jarvis's risk-aware critic. Personality: "
        + personality
        + "\nDomain: "
        + domain
        + "\nContext: "
        + json.dumps(context, ensure_ascii=False)
        + "\nProvide a concise critique with: risks, uncertainties, and counterpoints.\n\n"
        + "Tool Results:\n"
        + text
    )


def _build_plan_prompt(text: str, context: Dict[str, Any], domain: str, personality: str) -> str:
    return (
        "You are Jarvis's planner. Personality: "
        + personality
        + "\nDomain: "
        + domain
        + "\nContext: "
        + json.dumps(context, ensure_ascii=False)
        + "\nPropose 3-5 next actions as an ordered list, terse and practical.\n\n"
        + "Tool Results:\n"
        + text
    )


def _rule_based_reflection(results: List[Any], context: Dict[str, Any], domain: str) -> str:
    count = len(results)
    risks = []
    if domain == "trading":
        if any("volatility" in json.dumps(r).lower() for r in results):
            risks.append("High volatility detected — consider tighter risk controls.")
    pros = ["Multiple data points considered" if count > 1 else "Single source used"]
    cons = ["LLM unavailable, used rule-based summary"]
    return (
        f"Summary: Reflected over {count} result(s) in domain '{domain}'.\n"
        f"Pros: {', '.join(pros)}\nCons: {', '.join(cons)}\n"
        f"Confidence: 0.65\nSuggestions: 1) Verify assumptions 2) Add another source 3) Re-run with fresh data"
    )


def _rule_based_critique(results: List[Any], context: Dict[str, Any], domain: str) -> str:
    notes = []
    if domain == "trading":
        notes.append("Check position sizing and recent drawdown before acting.")
    notes.append("Data freshness not guaranteed; consider re-fetching.")
    return "; ".join(notes)


def _rule_based_plan(results: List[Any], context: Dict[str, Any], domain: str) -> str:
    steps = [
        "Gather one additional corroborating source",
        "Validate assumptions against recent history",
        "Draft a short recommendation and share with user",
    ]
    return "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))


if __name__ == "__main__":
    async def _test():
        agent = ReasonerAgent()
        await agent.start()
        task = TaskRequest(
            task_id="t1",
            agent_id=agent.agent_id,
            capability=AgentCapability.SYSTEM,
            task_type="reflect",
            parameters={"results": [{"metric": "volatility", "value": 0.3}], "domain": "trading"},
        )
        resp = await agent._handle_task(task)
        print(resp.result)
        await agent.stop()

    asyncio.run(_test())


