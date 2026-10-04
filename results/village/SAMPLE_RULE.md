# Village sample rule (written before any coder output)

**Chunks:** 216 in `data/village/main_in/` (152 incident, 64 control). Second coder: 32 (step 4, seed 0). Seed 0 throughout.

## Episodes and windows
Ricky chose all 32 catalogued episodes:
- E01-E23 from `episodes-v1.tsv`; E24-E32 from `episodes-v2-additions.tsv`.
- Plus the two episodes Anna suggested that are not in the catalog, the saboteur game and the hallucinated contact list.
- Anna's third suggestion, the Jul 6 pull request, is catalog E02.

Each episode's window is its room's chat:
- **Default:** t-2h to t+24h (UTC). E06 and E26 end at t+25h. E18 starts at t-135min.
- **Merged windows:** windows that overlap in one room form one unit, giving 6 merged units: E24+E08, E27+E28+E29+E14, E32+E19, E04+E20, E30+E31, E23+E22.
- **Saboteur game:** "Develop a turn-based RPG together while voting out Easter Egg saboteurs!". Rooms #general and #voted-out. Game days 2026-03-05, 06, 09, 10, 11, 12, 13.
- **Contact list:** o3's "93-address" list. #general, 2025-06-10 17:48:20 to 2025-06-11 19:48:20 UTC. t is o3's first claim, at 19:48:20.

## Chunks
- Whole messages, at most 24,000 characters including the system block. A chunk is cut at the largest time gap in its last 40%.
- Every chunk starts with the reporting/contact/approval lines of the agents' system prompt as of its first date, copied exactly from verbatim prompt copies in agent_memories:
  - 2025-06: short help@ line.
  - 2026-01 to 04-13: long help@ line. Inferred: no copy exists for this period.
  - 2026-04-14 to 08-24: help@ line plus the approval tool and outreach principles.
  - From 2026-08-25: adds the report@ line. September is inferred.
- **Private notes:** the focal agents' tool narration, interleaved as `(private_notes)`. This is their visible model text plus `#` bash comments; it contains no reasoning.
  - Focal agents: the catalog actor of each episode, o3 for the contact list, and each game day's self-revealed saboteurs (single-coded).
  - Control days carry the same agents' narration.
- **Credentials** were redacted (`[REDACTED-CREDENTIAL]`, 4 in this set). A key-shape scan of the final chunks found none left.

## How chunks were picked
Units are processed in time order with one `random.Random(0)`.
1. **Each catalogued unit:**
   - Keep the chunk holding each catalogued act time t (every act line is present).
   - Fill to 5 with a seeded sample of the unit's other incident chunks.
2. **Saboteur game:** 3 seeded chunks per game day (21).
3. **Contact list:** all 11.
4. **Controls:**
   - Candidate days are any UTC day in the unit's room within 7 days before or after the window, with 30 or more messages, that overlaps no catalogued window (E01-E32) or either of the two uncatalogued windows.
   - Every such day was chunked into the pool.
   - Per unit, `round(n_incident/2)` controls were drawn. Python rounds halves to even, so a 5-chunk unit gets 2.
   - Draws are a seeded sample of that unit's controls in the uncut build. Those were themselves a seeded sample, without replacement, of the pool.
5. Files are renumbered v000.. by first message time. `index.json` key `src_id` is the chunk's id in the uncut build (`main_in_all`, 1,900 chunks).

**"Calm" is unverified.** A control day only means that no catalogued incident overlaps it. The catalog is incomplete: the v2 audit estimates about 0.5 uncatalogued acts per room-day, 95% interval roughly 0-1. Controls for the game fall on days with other goals: 2026-02-26 and 03-02 to 03-04.

## Exact dates
- **Incident:**
  - 2025-06-10/11
  - 2026-03-05, 06, 09-13
  - 2026-04-03/04, 04-07/08, 04-08/09, 04-17/18
  - 2026-05-13/14, 05-28/29
  - 2026-06-11/12, 06-15/16
  - 2026-07-03/04, 07-06/07, 07-14/15, 07-21/22, 07-23/24, 07-27 to 07-29, 07-30 to 08-01
  - 2026-08-05/06, 08-07/08, 08-17/18, 08-27 to 08-29
  - 2026-09-01/02, 09-03/04, 09-11/12, 09-15/16
- **Control:**
  - 2025-06-03, 05, 06, 09, 17, 18
  - 2026-02-26
  - 2026-03-02, 03, 04, 27
  - 2026-04-06, 10, 14, 16, 22
  - 2026-05-12, 19, 27
  - 2026-06-04, 08, 09, 10, 29
  - 2026-07-08, 16, 17, 20
  - 2026-08-03, 04, 12, 14, 20, 21, 25, 26, 31
  - 2026-09-08, 10, 14
