"""models.py - the exact shapes we ask the AI to fill in (pydantic checks every answer)."""

from typing import Literal

from pydantic import BaseModel, Field


class Triage(BaseModel):
    summary: str = Field(description="two plain-English sentences: what is broken and who feels it")
    likely_cause: str = Field(description="the most likely cause, based only on the alert and the runbook")
    severity: Literal["SEV1", "SEV2", "SEV3", "SEV4"] = Field(description="SEV1 = customers fully down")
    customer_impact: str
    runbook_steps: list[str] = Field(max_length=8, description="steps copied from the runbook, in order")
    next_checks: list[str] = Field(max_length=5, description="what an engineer should look at next")


class TimelineEntry(BaseModel):
    time: str = Field(description="the time exactly as written in the notes, e.g. 02:14")
    event: str


class ActionItem(BaseModel):
    action: str
    owner_role: str = Field(description="a role such as 'DBA team', never a person's name")
    priority: Literal["P1", "P2", "P3"]


class Postmortem(BaseModel):
    title: str
    summary: str
    impact: str
    timeline: list[TimelineEntry] = Field(max_length=30)
    root_cause: str
    contributing_factors: list[str] = Field(max_length=6)
    what_went_well: list[str] = Field(max_length=5)
    what_went_wrong: list[str] = Field(max_length=5)
    action_items: list[ActionItem] = Field(max_length=8)
