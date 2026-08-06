from typing import Literal

from langfuse.openai import OpenAI
from pydantic import BaseModel

from copium.config.settings import settings
from copium.state import PipelineState, Category

MAX_BODY_CHARS = 4000

client = OpenAI(api_key=settings.OPENAI_API_KEY)


class Classification(BaseModel):
    reasoning: str   # quoted phrase that decided it, written before the label
    category: Category


def build_classify_prompt(state: PipelineState) -> str:
    body = (state.body or "No body text could be extracted.")[:MAX_BODY_CHARS]

    return f"""You are classifying a recruiting email sent to a job applicant.

Assign exactly one category:
- rejection: this application is closed. Includes explicit rejections, "moving forward
  with other candidates", and the role being filled or cancelled.
- advancement: the company wants a next step — interview, screening call, or assessment.
- acknowledgment: confirms the application was received. No decision made.
- offer: an offer of employment.
- other: anything else, such as account verification or a delay notice.

STRICT RULES:
- Only a decision already made counts as a rejection. Acknowledgments often contain
  conditional boilerplate like "if you are not selected for this position". That is a
  hypothetical, not a decision.
- Tone is not evidence. A rejection need not say "unfortunately". "Our team did not
  select you for further consideration" is a rejection.
- If an email closes one application but invites the candidate to a next step elsewhere,
  choose advancement. The invitation takes priority.
- Judge the email, not the sender. The same address sends both acknowledgments and
  rejections for the same role.
- The company must be the one ending it. If the candidate withdrew, or the email merely
  confirms an action the candidate took, that is not a rejection — use other.

Subject: {state.subject or "(no subject)"}
From: {state.sender or "(unknown sender)"}

Body:
{body}

Quote the phrase that decided it in "reasoning", then give the category."""


def classify_email(state: PipelineState) -> Classification:
    """Call the LLM to categorize the email, using structured output so the
    response is guaranteed to match the schema."""
    prompt = build_classify_prompt(state)

    completion = client.chat.completions.parse(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format=Classification,
        temperature=0,
    )
    return completion.choices[0].message.parsed


def classify_node(state: PipelineState) -> dict:
    """Categorize the email and derive the rejection flag the graph branches on.
    Only 'rejection' continues to extraction; everything else exits early."""
    result = classify_email(state)
    is_rejection = result.category == "rejection"

    print(f"  [classify] {result.category} — {result.reasoning}")

    return {
        "category": result.category,
        "is_rejection": is_rejection,
        "classification_reasoning": result.reasoning,
    }