from langfuse.openai import OpenAI
from pydantic import BaseModel

from copium.config.settings import settings
from copium.state import PipelineState

client = OpenAI(api_key=settings.OPENAI_API_KEY)


class Roast(BaseModel):
    reasoning: str     # why this fact is absurd next to a rejection
    chosen_fact: str   # the company fact built on, quoted from the list
    roast: str         # the card text


def build_roast_prompt(state: PipelineState) -> str:
    facts = "\n".join(f"- {f}" for f in (state.notable_facts or [])) or "None found."

    return f"""You write the caption for a card that appears on someone's phone after a job
rejection. The voice is dry and understated. The reader should laugh at what you noticed.

THE JOKE COMES FROM THE COMPANY, NEVER FROM THE REJECTION LETTER.

The person has already read the letter. They know it said "after careful review" and
"decided not to move forward." Repeating that back is worthless, and escaping it is the
entire point of this product. Never quote, paraphrase, or gesture at the letter's wording.
The only new information here is what was learned about the company. Build on that.

STEP 1 — READ EVERY FACT, THEN PICK ONE

Read the whole list before choosing, including the last item. The interesting fact is
rarely the first one.

Strong candidates: an acquisition. A new office in another country. A specific product
they killed. A marketing claim about efficiency, speed, or intelligence. A named list of
prestigious investors. A precise date. A stated mission or value.

Weak candidates, use only if nothing sharper exists: headcount, valuation, total funding
raised, annual revenue, year founded, headquarters. These are just size, and size is not
a joke. "They are big and rejected you" is the obvious frame and it is dead on arrival.

STEP 2 — WRITE TWO SENTENCES

The first states the fact plainly, in your own words, with real specifics. The second lands
against it and stops. The landing does not have to be about the applicant. Sometimes the
funnier move is to leave them out and let the company's own behavior close the joke.

EXAMPLES

These show the shape, not the wording. Do not reuse their sentence patterns, their
endings, or their phrasing.

FACTS: Meridian Labs acquired Toronto-based Kestrel Systems in March and opened new offices
in Berlin and Singapore.
CARD: Meridian Labs bought a company in Toronto and opened offices in Berlin and Singapore
this year. They have expanded in every direction except one.

FACTS: Halcyon shut down its consumer app in April to focus on enterprise customers.
CARD: Halcyon killed its consumer product in April to concentrate on enterprise. The focus
is going well.

FACTS: Cadence's platform claims to reduce hiring time by seventy percent.
CARD: Cadence sells software that cuts hiring time by seventy percent. They appear to be
using it.

FACTS: Orbital's stated mission is to make work feel human again.
CARD: Orbital's mission is making work feel human again. This was communicated by an
address that does not accept replies.

FACTS: None found.
CARD: There is almost nothing about this company anywhere on the internet. The rejection
was still processed on schedule.

What those share: one concrete detail, no contrast words, no explanation trailing the
landing, and a second sentence that closes instead of summarizing.

ACCURACY — A WRONG CARD IS WORSE THAN A BORING ONE

- Use ONLY the facts listed below.
- State them at exactly the strength given. Do not upgrade a fact to make a joke work. A
  company discontinuing its own email product is not abandoning email, and that product is
  not how the rejection was delivered.
- A high valuation alongside an older funding stage is not hypocrisy. Neither is hiring
  during layoffs unless the facts say both happened.
- You may draw a dry inference about the rejection itself. You may not invent facts about
  the company, and you may not invent details about the hiring process such as how long it
  took or who reviewed it.
- If you cannot be funny without stretching a fact, write the boring true version.

DELIVERY RULES

- 2 sentences. A third only if it is very short and lands.
- No contrast connectives: yet, however, but, meanwhile, despite, while, still, though.
- Do not use the words ironic or irony. Do not use unfortunately, which softens the
  landing rather than delivering it.
- No em-dashes. No exclamation marks. No rhetorical questions.
- Do not end every card on the applicant. Vary where the second sentence lands.
- Never name or target an individual.
- Do not be contemptuous about the applicant.
- Write out large round numbers as words when it reads better.

INPUT

Company: {state.company_name}
What they do: {state.what_they_do or "Unknown."}
Role they rejected you from: {state.role}

Facts about the company:
{facts}

Name the fact you built on in "chosen_fact", quoted from the list above. Then write the
card text."""


def write_roast(state: PipelineState) -> Roast:
    """Generate the card caption from the researched company facts."""
    prompt = build_roast_prompt(state)

    completion = client.chat.completions.parse(
        model=settings.ROAST_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format=Roast,
    )
    return completion.choices[0].message.parsed


def roast_node(state: PipelineState) -> dict:
    """Write the roast. Requires research to have run first, though it degrades
    gracefully to roasting the company's obscurity when no facts were found."""
    if not state.company_name:
        raise ValueError(
            f"roast_node called without a company name for "
            f"message {state.message_id} — check the graph's edge order"
        )

    result = write_roast(state)
    print(f"  [roast] built on: {result.chosen_fact}")
    print(f"  {result.roast}")

    return {
        "roast": result.roast,
        "roast_source_fact": result.chosen_fact,
    }