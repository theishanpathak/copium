# Copium

Job rejections, read and roasted automatically.

A rejection email lands in Gmail. About thirty seconds later a card is on my phone: the
company's actual rejection sentence, struck through, with two sentences underneath in
which the company says something faintly ridiculous about itself.

**[See the published ones →](https://copium-beta.vercel.app/wall)**

---

## How it works

```
Gmail  ──watch()──►  Pub/Sub  ──push──►  Vercel webhook
                                              │
                                    repository_dispatch
                                              │
                                              ▼
                                      GitHub Actions
                                              │
   ┌──────────────────────────────────────────┘
   ▼
resolve  ─►  fetch  ─►  ┌─ LangGraph ─────────────────────────┐
(historyId    (parse)   │  classify ─► extract ─► research ─► │ ─► Supabase ─► Web Push
 diff)                  │      │        (LLM)     (Tavily)  roast │
                        │      └─► END if not a rejection        │
                        └──────────────────────────────────────┘
```

Gmail's `watch()` publishes to a Pub/Sub topic whenever the mailbox changes. A Vercel
route receives the push and fires a `repository_dispatch`, which runs the pipeline in
GitHub Actions.

The graph classifies the email, and anything that isn't a rejection exits immediately —
no extraction, no search, no writing. Rejections continue: company and role are pulled
out, two web searches gather recent facts, and a final call writes the card.

---

## Design notes

**Push, not polling.** Gmail's `watch()` fires on any mailbox change, so nothing is on a
schedule. The subscription expires after seven days and a daily cron renews it, which
gives six consecutive failures of margin before anything breaks.

**The notification doesn't say which email arrived.** Pub/Sub delivers a `historyId`
representing the mailbox *after* the change, which is useless for finding what changed.
The pipeline stores its own cursor and calls `history.list()` to diff, falling back to a
recency window on the first run and whenever the cursor outlives Gmail's roughly one-week
history retention.

**Deduplication happens three times.** A single email produces three or four history
events. The cursor filters most of them, a `processed_messages` table keyed on the Gmail
message id claims each message before any LLM call so concurrent runs skip rather than
duplicate work, and the final insert is idempotent. Claims are released on failure so a
crashed message is retried rather than silently lost.

**Early exit is the cost control.** Acknowledgments are the majority of what arrives in a
job-hunting inbox and they cost exactly one classifier call.

**Three models, chosen by task.** `gpt-4o-mini` handles classification and extraction,
which are mechanical and score near-perfectly against a labelled fixture set. The roast
uses a stronger model, because deadpan comedy under tight constraints is the one place
where capability visibly changes the output. Roughly ten rounds of prompt tuning on the
cheaper model never fixed a template it kept falling into; changing the model did, in one
run.

**The nodes are pure.** Fetching, storage, and message resolution all happen outside the
graph, so every node is `state -> dict` with no I/O. That is what made individual nodes
testable without standing up the pipeline.

**Parsing bit harder than expected.** LinkedIn sends a 2 KB plain-text part containing
only navigation and a 143 KB HTML part containing the actual rejection. Preferring
`text/plain` meant the classifier was reading footer links, and the extractor was
picking up my own LinkedIn headline as the job title. The parser now compares how much
readable text each part carries, ignoring URLs, and takes whichever actually says
something.

---

## Evaluation

Classification and extraction are scored against a hand-labelled set of 45 real
recruiting emails. That set and the scripts that run it are kept out of this repo,
since the emails carry real recruiter names, company names, and my own address.

The set exists because keyword matching fails in both directions. Acknowledgments
routinely contain rejection vocabulary conditionally — *"if you are not selected for
this position"* — while real rejections often contain none at all: *"our team did not
select you for further consideration."* Six companies appear twice with opposite labels,
same sender and same template family, which is why sender identity carries no signal.

Both prompts were adjusted to fix cases inside that set, so the honest number comes from
emails labelled after the prompts were frozen.

---

## Stack

| | |
|---|---|
| Pipeline | Python, LangGraph, OpenAI SDK |
| Search | Tavily |
| Tracing | Langfuse |
| Storage | Supabase |
| Frontend | Next.js, Tailwind, deployed on Vercel |
| Runtime | GitHub Actions |
| Delivery | Web Push, installable PWA |

---

## Running your own

Copium reads one specific inbox, so there is no hosted version. Gmail's read scope is
restricted, which means a public multi-tenant deployment would need an annual third-party
security assessment. Personal use is exempt, so the intended path is running your own.

You will need a Google Cloud project with the Gmail API enabled, a Pub/Sub topic and push
subscription, OAuth credentials, and keys for OpenAI, Tavily, and Supabase. Copy both
`.env.example` files and fill them in.

```bash
cd backend && uv sync
uv run python -m copium.gmail_watch    # register the push subscription
uv run python main.py                  # process anything new
```

---

## Known limits

- One user. Tokens live in environment variables rather than per-user storage.
- The relevance gate falls back to a five-minute window when no cursor exists, which is a
  heuristic rather than a guarantee.
- Interview invites and offers send a notification but produce no card. They are
  time-sensitive, and a joke is the wrong response.
- Cards are reviewed by hand before publishing. Roughly seven in ten are worth keeping.