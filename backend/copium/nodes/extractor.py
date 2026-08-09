from langfuse.openai import OpenAI
from pydantic import BaseModel

from copium.config.settings import settings
from copium.log import detail, step
from copium.state import PipelineState

MAX_BODY_CHARS = 4000

client = OpenAI(api_key=settings.OPENAI_API_KEY)


class Extraction(BaseModel):
    reasoning: str   # where in the email the company/role came from
    company_name: str
    role: str


def build_extract_prompt(state: PipelineState) -> str:
    body = (state.body or "No body text could be extracted.")[:MAX_BODY_CHARS]

    return f"""You are extracting the company name and job role from a rejection email.

COMPANY NAME

- The company is who is REJECTING the candidate, not necessarily who the email is FROM.
  Sender names are often a person's name, a recruiting platform, or a hiring team label.
  Read the body to confirm.
- Give the name the company is actually known by. Drop legal and descriptive suffixes
  that are not part of the brand: Inc, LLC, Ltd, Corp, Corporation, Incorporated,
  Company, Group, Holdings, Technologies. "Samsung Company" is "Samsung".
  "Pogo Technologies, Inc." is "Pogo Technologies".
- Keep such a word only when the brand genuinely includes it, as in "Boston Consulting
  Group", "The Coca-Cola Company", or "Warner Bros.".
- The body may use a shortened form ("Solve" for "Solve Intelligence", "Scale" for
  "Scale AI"). Check the subject line and sender field for a longer form of the same
  name and prefer that.

ROLE

- Use the job title as the company writes it.
- Strip requisition numbers and ID codes, typically a standalone or year-prefixed number
  before or after the title: "2026-86955 - Software Development Engineer" becomes
  "Software Development Engineer".
- Keep level and team qualifiers, which are part of the title: "Software Engineer 1 -
  DSP Runtime" stays whole, because "1" is a level and "DSP Runtime" is a team.
- If the role cannot be determined from the text, use "Unknown Role". Do not guess.

Subject: {state.subject or "(no subject)"}
From: {state.sender or "(unknown sender)"}

Body:
{body}

Explain in "reasoning" where you found the company and role, then extract both."""

def extract_email(state: PipelineState) -> Extraction:
    """Call the LLM to pull company_name and role from a confirmed rejection."""
    prompt = build_extract_prompt(state)

    completion = client.chat.completions.parse(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format=Extraction,
        temperature=0,
    )
    return completion.choices[0].message.parsed


def extract_node(state: PipelineState) -> dict:
    """Extract company_name and role. Only valid on a confirmed rejection —
    the graph's conditional edge is what enforces that upstream."""
    if not state.is_rejection:
        raise ValueError(
            f"extract_node called on a non-rejection ({state.category}) "
            f"for message {state.message_id} — check the graph's edge logic"
        )

    result = extract_email(state)
    step("extract", "ok")
    detail(f"{result.company_name} — {result.role}")
    detail(result.reasoning)

    return {
        "company_name": result.company_name,
        "role": result.role,
    }