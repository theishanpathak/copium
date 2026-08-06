from langfuse.openai import OpenAI
from pydantic import BaseModel

from copium.config.settings import settings
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

STRICT RULES:
- The company is who is REJECTING the candidate, not necessarily who the email is FROM.
  Sender names are often a person's name, a recruiting platform, or a hiring team label —
  read the body to confirm the actual company.
- Strip legal suffixes from the company name unless they're clearly part of the brand
  (e.g. "Pogo Technologies, Inc." -> "Pogo Technologies", but "Warner Bros." stays as is
  if that's how the company refers to itself).
- If the role truly cannot be determined from the text, use "Unknown Role" rather than
  guessing. Do not invent a role that isn't stated or clearly implied.
- Strip requisition/req numbers and ID codes from the role — these are typically a
  standalone number or a year-prefixed code, either before or after the title
  (e.g. "2026-86955 - Software Development Engineer" -> "Software Development
  Engineer"). Do NOT strip a short qualifier that's part of how the company names the
  role itself, such as a level or team designation (e.g. "Software Engineer 1 - DSP
  Runtime" stays whole — "1" is a level, "DSP Runtime" is a team, neither is a req code).
- The company name may appear in a shortened form in the body (e.g. "Solve" for "Solve
  Intelligence", "Scale" for "Scale AI"). Before finalizing the company name, check the
  subject line and the sender field for a longer form of the same name, and use that
  fuller form if one exists.

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
    print(f"  [extract] {result.company_name} — {result.role} — {result.reasoning}")

    return {
        "company_name": result.company_name,
        "role": result.role,
    }