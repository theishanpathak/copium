import re

from datetime import date
from langfuse.openai import OpenAI
from pydantic import BaseModel
from tavily import TavilyClient

from copium.config.settings import settings
from copium.log import detail, step
from copium.state import PipelineState

client = OpenAI(api_key=settings.OPENAI_API_KEY)
tavily = TavilyClient(api_key=settings.TAVILY_API_KEY)

MAX_RESULTS = 4
MAX_CONTENT_CHARS = 600

_STOPWORDS = {"the", "and", "inc", "llc", "ltd", "corp", "company"}


class Research(BaseModel):
    reasoning: str            # which results were useful, which were noise
    what_they_do: str         # one plain sentence, no buzzwords
    notable_facts: list[str]  # concrete and specific, each from a result
    has_material: bool        # false when results were empty or useless

def search_news(company: str) -> list[dict]:
    """Recent news about the company. No topical keywords — they outrank the
    entity in news search and return generic industry coverage instead."""
    response = tavily.search(
        f'"{company}" company announcement',
        topic="news",
        time_range="year",
        max_results=MAX_RESULTS,
    )
    return _relevant(company, response.get("results", []))


def search_overview(company: str) -> list[dict]:
    """What the company does and what it has been doing. Deliberately avoids
    funding and headcount keywords, which crowd out more specific material."""
    response = tavily.search(
        f"{company} company products launch acquisition customers offices",
        max_results=MAX_RESULTS,
    )
    return _relevant(company, response.get("results", []))


def _format_results(label: str, results: list[dict]) -> str:
    """Render one search's results as numbered, truncated text for the prompt."""
    if not results:
        return f"{label}: No results found."

    lines = [f"{label}:"]
    for i, r in enumerate(results):
        content = r.get("content", "")[:MAX_CONTENT_CHARS]
        lines.append(f"  {i}. {r.get('title', '(no title)')}\n     {content}")
    return "\n".join(lines)


def _needles(company: str) -> set[str]:
    """Match strings for relevance.

    Includes the brand token as well as the full name, so a result about
    "Samsung" still counts when extraction returned "Samsung Electronics
    America". Full-string matching alone drops everything for multi-word names.
    """
    lowered = company.lower().strip()
    tokens = [
        token
        for token in re.split(r"[^a-z0-9]+", lowered)
        if len(token) >= 3 and token not in _STOPWORDS
    ]

    needles = {lowered}
    if tokens:
        needles.add(tokens[0])
    return needles


def _relevant(company: str, results: list[dict]) -> list[dict]:
    """Drop results that never mention the company.

    Tavily's filters guarantee results come back even when nothing matches, so
    a name-presence check is the only thing separating real hits from filler.
    """
    needles = _needles(company)

    return [
        result
        for result in results
        if any(
            needle in result.get("title", "").lower()
            or needle in result.get("content", "").lower()
            for needle in needles
        )
    ]


def build_research_prompt(state: PipelineState, searches: dict[str, list[dict]]) -> str:
    blocks = "\n\n".join(
        _format_results(label, results) for label, results in searches.items()
    )

    return f"""You are gathering factual material about a company that just rejected a
job applicant. Another system will write the jokes. Your only job is accurate facts.

Today is {date.today().isoformat()}.

SOURCES

- Use ONLY the search results below. Do not add outside knowledge about this company.
- Some results will be about a different company with a similar name, or about the
  industry in general. Ignore those and say which in reasoning.
- If the results do not contain enough real information about this specific company,
  set has_material to false. Do not pad with generic industry statements.

WHAT MAKES A GOOD FACT

- Specific over vague: "raised $20M led by Sequoia", not "well-funded". Prefer numbers,
  names, and dates over adjectives.
- Neutral. No jokes, no commentary, no editorialising.

RECENCY

- Prefer facts from the last 18 months. A product launch or acquisition from three years
  ago is not news and should be dropped.
- Foundational facts are exempt when still true: when the company was founded, what it
  fundamentally does.
- Include the date inside the fact text whenever the result gives one.
- When two facts conflict, report only the more recent and note the conflict in
  reasoning.
- If a result gives no date, do not guess. Include it only if it is clearly still true.

Company: {state.company_name}
Role the applicant was rejected from: {state.role}

{blocks}

Summarize what is actually known about this company from the results above."""

def research_company(state: PipelineState) -> Research:
    """Run the searches, then summarize into grounded facts."""
    company = state.company_name or ""

    searches = {
        "RECENT NEWS": search_news(company),
        "COMPANY OVERVIEW": search_overview(company),
    }

    prompt = build_research_prompt(state, searches)

    completion = client.chat.completions.parse(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format=Research,
        temperature=0,
    )
    return completion.choices[0].message.parsed


def research_node(state: PipelineState) -> dict:
    """Gather grounded facts about the rejecting company. Requires extraction
    to have run first — the graph's edge order is what enforces that."""
    if not state.company_name:
        raise ValueError(
            f"research_node called without a company name for "
            f"message {state.message_id} — check the graph's edge order"
        )

    result = research_company(state)
    step("research", f"material={result.has_material} facts={len(result.notable_facts)}")
    detail(state.company_name or "")

    return {
        "what_they_do": result.what_they_do,
        "notable_facts": result.notable_facts,
        "has_research_material": result.has_material,
    }