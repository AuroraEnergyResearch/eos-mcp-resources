# Gates: what to ask and what to pass

`prepare_scenarios.py` enforces three gates. Each exits without writing anything until the user has decided and the matching flag is passed. Ask in chat first; pass a flag only after the user's answer.

## Gate 2: the entry limit (exit 2)

One price zone counts as one entry, so a scenario with 12 zones is 12 entries. The limit is **24**, which is two Nordic scenarios with 12 zones each. Beyond it, say so plainly and ask which entries to drop. There is no flag.

## Gate 3: token cost against data (exit 3, flag `--tradeoff-confirmed`)

Trips above **18** entries. The user makes the trade-off explicitly: a general "yes" to the selection is not the decision. Give the numbers first.

- **Cost model** (fitted to measured runs, within about 15%): about 8k tokens fixed, plus 5k per scenario looked up (9k when the scenario is split into zones), plus 2.4k per entry (two download links of about 1.2k tokens each). A Weather Year family is inspected once, so each further member adds only about 0.4k for its list record. Examples: 3 scenarios by 6 zones (18 entries) is about 78k tokens; two Nordic scenarios by 12 zones (24 entries) is about 84k; 18 unrelated scenarios is about 141k, because each needs its own look-up; an 18-member Weather Year family is about 63k.
- **Data cost**: every entry adds a line to every chart, and charts read best at 8 to 10 lines or fewer.

Offer: keep all *N* (most data, most tokens); narrow to 18 (name the saving, about 2.4k tokens per entry removed); or choose which zones or scenarios to keep. Say what narrowing drops, for example "this drops SIC from all three scenarios". Pass `--tradeoff-confirmed` only after they choose to keep more than 18.

Up to 18 entries need no confirmation.

## Gate 4: currency years (exit 4, flag `--currency-year-confirmed`)

Trips when scenarios share a currency base but default to different year codes. Older and newer scenarios often do: EUR 2021 real against EUR 2025 real; `gbp2024` for GB Oct 25 against `gbp2025` for GB Q4 26. Ask which currency year each scenario shows, based on what each offers.

- Read each scenario's `currency_codes`. Show the calendar-year options per scenario ("A offers EUR 2019 to 2023 real; B offers EUR 2019 to 2026 real") and mention that monthly codes such as `eur2025jan` also exist.
- Offer with `ask_user_input_v0`: (1) one shared year for all, naming the most recent calendar year every scenario offers; (2) each scenario in its own default, naming each, with the note that levels are then not strictly like for like; (3) a year chosen per scenario (then ask for the years). When no year is shared by all, say so.
- No question when every scenario already defaults to the same code.
- Different bases (GBP against EUR) share no code: use each scenario's default and let the page state the mismatch. When one scenario offers several bases (a pan-European run with EUR, GBP and PLN), ask which base it shows in.
- Origin restates values into the requested currency; the skill converts nothing. Put the chosen code in each manifest entry's `currency`, and `currencyType` from the inspect result in `currency_type` (financial-year codes such as `aud2023` are labelled "financial year").
