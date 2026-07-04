# Fake Data

All files in this directory are **fake, manually generated JSON files** used by the
Sports Agent Governance Gateway.

- The organization **Northstar Athletics** is fictional.
- No real sports team, league, ticketing API, CRM, or fan data is used.
- The teams, venues, players, fans, tickets, and content records are invented for
  demonstration purposes only.

## Files

| File                    | Description                                        |
| ----------------------- | -------------------------------------------------- |
| `schedule.json`         | Fake upcoming events for the fictional venue.      |
| `policies.json`         | Fake venue policies (bag, parking, accessibility). |
| `tickets.json`          | Fake ticket inventory tied to events.              |
| `fans.json`             | Fictional fan profiles (invented people).          |
| `content_library.json`  | Fake content records (clips, interviews, posts).   |
| `visual_assets.json`    | Fake visual assets with pre-computed classifications. |

You can freely edit these files locally to experiment with the gateway. The tools
read directly from these JSON files at request time, so no rebuild is required.
