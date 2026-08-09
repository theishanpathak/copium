from langfuse.openai import OpenAI
from pydantic import BaseModel

from copium.config.settings import settings
from copium.log import detail, step
from copium.state import PipelineState

client = OpenAI(api_key=settings.OPENAI_API_KEY)


class Roast(BaseModel):
    reasoning: str          # why this fact works, written before the card
    chosen_fact: str        # the fact built on, quoted from the list
    first_sentence: str     # the company stating something true about itself
    second_sentence: str    # the flat admission that undercuts it


def build_roast_prompt(state: PipelineState) -> str:
    facts = "\n".join(f"- {f}" for f in (state.notable_facts or [])) or "None found."

    return f"""You write two sentences for a card that appears after a job rejection. The
card shows the company's real rejection line struck through, then these two sentences
underneath, as though the company had written them instead.

THE IDEA

This is a coping mechanism and it says so on the tin. The applicant did not get the job.
What they get instead is the company, in its own corporate voice, saying something
faintly ridiculous about itself. The company is the one who ends up looking silly. That
is the entire trick.

VOICE

Write as the company: we, our, us. Corporate register, delivered completely straight.
Never "you" or "your" — the applicant is never addressed and never mentioned. Never "I".

First sentence: a real fact about us, stated the way a company states things.
Second sentence: still our voice, still flat, landing somewhere a press release would not.

WHAT THE SECOND SENTENCE CAN DO

- Follow the fact one step further than we meant it to go.
- Admit something the fact already implies.
- Refer to the rejection, if the line is specific and dry.

WHAT IT CANNOT DO

- Invent anything. Office snacks, coffee machines, plants, voicemail: not on the
  list of facts, so they did not happen. If the second sentence introduces
  something not listed below, it is wrong.

- Compare us to ourselves. Any sentence meaning "we are good at X, our hiring is
  worse" is banned in every phrasing: does not extend to, unlike our, in contrast,
  parallels, remains better at, is less. Do not use the words hiring, recruiting,
  interviewing, candidates, applicants, selection, or decision-making process.

- Change the subject. Both sentences are about the same fact. The second follows
  it one step further than a press release would go.

EXAMPLES

EXAMPLES

FACTS: Northbridge Advisors formed a national division to manage partnerships.
CARD: We have formed a national division to manage partnerships. We have become very good
at saying no.

FACTS: Halcyon Storage has already sold its entire 2026 production capacity of hard disk
drives.
CARD: We have already sold our entire 2026 production of hard drives. We now face the
intriguing problem of manufacturing them.

FACTS: Quillon is discontinuing its email product because user behaviour has moved toward
AI agents.
CARD: We are shutting down our email product because nobody uses email the way they used
to. This message was sent by email.

FACTS: Merrow Financial acquired a Canadian crypto firm for C$250 million.
CARD: We acquired a Canadian crypto firm for two hundred and fifty million dollars. It
remains our most expensive welcome to date.

FACTS: Ardent Auctions' former chief executive has reassumed the role after his
successor departed.
CARD: Our former chief executive has reassumed the role of chief executive. We prefer a
familiar face.

FACTS: Loom Logistics' sixty staff will merge into a thousand-person regional team.
CARD: Our sixty employees will shortly join a team of one thousand. We may need name
tags.

FACTS: Sable Telecom is relocating its global headquarters twenty miles over three years.
CARD: We are moving our headquarters twenty miles over the next three years. We expect to
arrive in 2029.

FACTS: None found.
CARD: There is very little about us anywhere on the internet. We prefer to let our
correspondence speak for us.

ACCURACY

- Use ONLY the facts listed below. Do not invent anything about the company.
- State facts at the strength given. Do not exaggerate to make a joke work.
- Do not invent details about the hiring process: how long it took, who read it, whether
  a person or a machine handled it.
- Never name an individual unless the facts name them.
- If you cannot be funny without stretching a fact, write the boring true version.

FORM

- First person plural throughout: we, our, us. Never "you", never "your", never "I".
- No emoji. No exclamation marks. No rhetorical questions.
- Do not use the words ironic, irony, or unfortunately.
- Write large round numbers as words when it reads better.

THE FACTS

Company: {state.company_name}
What we do: {state.what_they_do or "Unknown."}
Role being declined: {state.role}

About us:
{facts}

Name the fact you built on in "chosen_fact". Then write the two sentences, one per
field."""

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
    roast = f"{result.first_sentence.strip()} {result.second_sentence.strip()}"

    step("roast", f"{len(roast)} chars")
    detail(f"built on: {result.chosen_fact}")
    detail(roast)

    return {"roast": roast, "roast_source_fact": result.chosen_fact}