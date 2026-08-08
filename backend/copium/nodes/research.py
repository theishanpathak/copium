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


class Research(BaseModel):
    reasoning: str            # which results were useful, which were noise
    what_they_do: str         # one plain sentence, no buzzwords
    notable_facts: list[str]  # concrete and specific, each from a result
    has_material: bool        # false when results were empty or useless


def _relevant(company: str, results: list[dict]) -> list[dict]:
    """Drop results that never mention the company.

    Tavily's filters guarantee results come back even when nothing matches, so a
    name-presence check is the only thing that distinguishes real hits from filler.
    """
    needle = company.lower()
    return [
        r
        for r in results
        if needle in r.get("title", "").lower()
        or needle in r.get("content", "").lower()
    ]


def search_news(company: str) -> list[dict]:
    """Recent news about the company. No topical keywords — they outrank the
    entity in news search and return generic industry coverage instead."""
    response = tavily.search(
        f'"{company}" company announcement',
        topic="news",
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


def build_research_prompt(state: PipelineState, searches: dict[str, list[dict]]) -> str:
    blocks = "\n\n".join(
        _format_results(label, results) for label, results in searches.items()
    )

    return f"""You are gathering factual material about a company that just rejected a
job applicant. Another system will write the jokes — your only job is accurate facts.

STRICT RULES:
- Use ONLY the search results below. Do not use outside knowledge about this company.
- Be specific. Prefer "raised $20M led by Sequoia" over "well-funded". Prefer numbers,
  dates, and names over adjectives.
- Do not write jokes, insults, or commentary. Neutral facts only.
- If the results do not contain enough real information about this specific company,
  set has_material to false. Do not pad with generic industry statements.
- Some results may be about a different company with a similar name, or about the
  industry generally. Ignore those and say so in reasoning.
- Search results may include outdated figures alongside current ones. When two facts
  conflict (e.g. an old funding stage next to a much later valuation), report only the
  most recent and note the conflict in reasoning. Prefer facts with dates attached.

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