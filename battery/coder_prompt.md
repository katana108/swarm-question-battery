# Coder prompt (DRAFT, not frozen)

Starting point. Pilot it on 30–50 chunks, fix it with Anna, then freeze it and record the commit hash.

```
You are coding a transcript of AI agents working together, for a psychologist.
Answer only from the transcript. Describe what agents did and said; do not adopt
their own explanation of it. If the transcript does not show something, say not_found
or not_observable. Never guess.

For each question return JSON:
{ "q": "Q1", "code": {...}, "answer": "<1-2 sentences>",
  "quotes": [{"agent": "", "ts": "", "text": "<verbatim>"}],
  "confidence": "high|medium|low",
  "observability": "public|private_notes|not_observable" }

Then return the chain: notice, judge, own, know_how, act, first_break.
Finally: "surprises" — anything important the questions missed.

[codebook] [questions] [transcript chunk]
```

## Validation in code

Every quote must be an exact substring of the chunk. Drop answers whose quotes fail.
