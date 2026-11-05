# Star Citizen Game.log signal catalog

This extraction draft combines the ALICE parser baseline with findings from VerseKit by Xharig and Bedrock by SC-Ravaxx. The public package can carry this catalog alongside a build-tagged fixture for each supported format.

**Evidence status.** “ALICE” means supported by the current implementation or explicitly identified in our session notes. “Upstream” means a recognizer or interpretation was inspected in the linked source. It still needs an independently reviewed, redacted game sample before we promise support. Cross-project agreement is useful corroboration even when the original captures are unavailable.

## Signals and their limits

| Family | Combined findings | Package decision |
| --- | --- | --- |
| Sessions and shards | ALICE has log start, quit and mode changes. VerseKit recognizes a PU join with a shard identifier and omits the network address. Bedrock uses a closing loading screen as system context. | Keep start, quit and mode. Candidate shard-join observation with timestamp and optional shard identifier. Treat a loading-screen close as its own observation. [VerseKit shard parsing][vk-shard] · [Bedrock game state][bed-state] |
| Contracts | ALICE has objective markers, share pushes, HUD notices and mission endings. VerseKit recognizes acceptance through localized HUD text and associated mission metadata. It excludes shared offers with a null mission ID and handles duplicate acceptance notices. | Add acceptance after validating the HUD framing and continuation lines. Preserve observed mission IDs. Keep deduplication in the consumer or a separate reducer. [VerseKit contracts][vk-contract] · [VerseKit mission scan][vk-mission] |
| Blueprints | Bedrock recognizes the English receipt notice and handles quotes inside a blueprint name. VerseKit supports localized receipt phrases and separately infers which mission supplied a reward. | Emit a receipt observation with the name as displayed. Test punctuation and localization. Keep contract attribution separate and label it inferred. [Bedrock blueprint library][bed-bp] · [VerseKit blueprint phrases][vk-phrases] · [VerseKit mission scan][vk-mission] |
| Item shops | ALICE parses item-buy requests and shop flow responses. VerseKit also recognizes item-shop sell requests and a selling response discriminator. | Add an item-sale request after capturing a sample. Inspect the existing response model for a compatible flow field. Preserve request and response separately. [VerseKit stock journal][vk-stock] |
| Commodity trades | ALICE captures buy and sell requests and observed buy rejection responses. Buy quantities arrive in centi-SCU and sell quantities arrive in SCU. VerseKit's stock journal excludes commodity sales because it lacks a success response to match. | Preserve requests and rejection observations. A timed correlation stays a heuristic. [ALICE formats][alice-events] · [VerseKit stock journal][vk-stock] |
| Inventory | ALICE captures queued operations, move details and completion. ALICE's asset tracker and VerseKit both match completions on request ID plus operation kind. VerseKit recognizes an additional queued-event tag and reports missing or reversed move-detail records. | Validate the additional tag and conflicting endpoints against captures. Keep observations separate so consumers can audit discrepancies. Inventory deltas lack a starting balance. [Current event reference][alice-events] · [VerseKit stock journal][vk-stock] |
| Place and travel | ALICE captures landing ID changes and inventory location names. VerseKit also learns code-to-ID pairs from ATC lines and nearby inventory lines. Bedrock distinguishes target selection, route origin and quantum arrival, and uses nearby zone helpers and nonzero terrain cell counts as body evidence. | Expose each validated observation independently. Keep map resolution, temporal joins and current-location estimates outside the core. [VerseKit location][vk-location] · [Bedrock game state][bed-state] |
| Ships | ALICE captures spawning, seat exit, kiosk selection and some class evidence. Our notes already contain a verified crew-channel example. Bedrock tracks join and leave notices, distinguishes player-triggered navigation from traffic for nearby ships, and recognizes ejection from a destroyed vehicle. | Capture crew transitions, player-triggered navigation and destroyed-vehicle ejection separately. Ejection evidence covers the case where an actor was inside. Avoid exposing owner names by default. [ALICE formats][alice-events] · [Bedrock game state][bed-state] |
| Mining | Bedrock recognizes gadget placement on a mineable entity and attachment to a hand. The same attachment can happen before placement or after retrieval. Placement can produce two notices. | Emit placement and attachment as observations after sample validation. A separate reducer can use the gadget entity ID and prior state to infer retrieval or collapse duplicate placement notices. [Bedrock game state][bed-state] |

## Extraction order

1. Move the existing standard-library parser, event types, watcher, dispatcher and path discovery into the shared package. Keep historical playback distinct from live events. Move only reviewed fixtures. ALICE-specific resolution and ledger logic stay in ALICE.
2. Validate blueprint receipt, crew-channel transitions, PU shard join and item-sale requests first. They have identifiable source records and useful tests without a world-state model. Then validate contract acceptance, travel observations and mining transitions.
3. Add a test for each observed format and its closest misleading case. Start with an embedded quote in a blueprint name, a shared offer with no mission ID, a shop sale beside a commodity sale, another ship's navigation traffic, a gadget attachment before placement, and overlapping inventory request numbers.
4. Document build, channel, language, source project and review status for each example. Use synthetic values for player names, IDs, server addresses and other session details. Keep raw logs out of the repo. Ask maintainers for redacted examples of cases that lack independent evidence when sharing the catalog.

## Source and credit

The upstream links are pinned to the inspected revisions. Both checkouts contain a GPLv3 license. This draft describes observed behavior and design lessons in original wording. Any future reuse of code or fixtures needs a license and attribution decision before it enters the public package. [VerseKit license][vk-license] · [Bedrock license][bed-license]

[alice-events]: event-reference.md
[vk-shard]: https://github.com/Xharig/VerseKit/blob/8e102e2c86fa886f48154dc78867541b73395fcc/crates/versekit-core/src/shard.rs
[vk-contract]: https://github.com/Xharig/VerseKit/blob/8e102e2c86fa886f48154dc78867541b73395fcc/crates/versekit-core/src/contracts.rs
[vk-mission]: https://github.com/Xharig/VerseKit/blob/8e102e2c86fa886f48154dc78867541b73395fcc/crates/versekit-core/src/mission_scan.rs
[vk-phrases]: https://github.com/Xharig/VerseKit/blob/8e102e2c86fa886f48154dc78867541b73395fcc/crates/versekit-core/src/phrases.rs
[vk-stock]: https://github.com/Xharig/VerseKit/blob/8e102e2c86fa886f48154dc78867541b73395fcc/crates/versekit-core/src/stock_journal.rs
[vk-location]: https://github.com/Xharig/VerseKit/blob/8e102e2c86fa886f48154dc78867541b73395fcc/crates/versekit-core/src/location.rs
[vk-license]: https://github.com/Xharig/VerseKit/blob/8e102e2c86fa886f48154dc78867541b73395fcc/LICENSE
[bed-state]: https://github.com/SC-Ravaxx/Bedrock/blob/cf6b13d7d435c151bc89d1ef55ea3f4d148e7422/src/GameState.cpp
[bed-bp]: https://github.com/SC-Ravaxx/Bedrock/blob/cf6b13d7d435c151bc89d1ef55ea3f4d148e7422/src/BlueprintLibrary.cpp
[bed-license]: https://github.com/SC-Ravaxx/Bedrock/blob/cf6b13d7d435c151bc89d1ef55ea3f4d148e7422/LICENSE
