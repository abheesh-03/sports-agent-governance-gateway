# Fake Data

Everything this project reads as "business data" is **fake** and lives as static
JSON files in the [`data/`](../data) directory.

## Guarantees

- All data is fictional and manually generated.
- The organization **Northstar Athletics** is invented.
- No real sports team, league, venue, or player is represented.
- No real ticketing, CRM, or payment system is used or integrated.
- No real people are represented — fan profiles are invented.
- No affiliation with any real company is claimed.

## Data files

| File                   | Contents                                             |
| ---------------------- | ---------------------------------------------------- |
| `schedule.json`        | Fake upcoming events (teams, dates, venue).          |
| `policies.json`        | Fake venue policies (bag, parking, accessibility).   |
| `tickets.json`         | Fake ticket inventory tied to events.                |
| `fans.json`            | Fictional fan profiles (invented names).             |
| `content_library.json` | Fake content records (clips, interviews, posts).     |

## How the data is used

The tools in [`tools/`](../tools) read these files directly (cached in memory)
at request time. There is no database of business data — only the audit log and
approval queue are persisted in SQLite.

## Editing the data

You can freely edit any JSON file locally to experiment with the gateway. For
example, add an event to `schedule.json` or a listing to `tickets.json`. Because
the tools read the files at runtime, no rebuild is required (a process restart
clears the in-memory cache).

## What this project is not

- It is not a production client system.
- It does not use real sports team data.
- It does not integrate with real ticketing or CRM systems.
- It does not require Claude, OpenAI, or any paid API for version 1.
