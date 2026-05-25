---
name: stock-workflow-schema
description: Use when defining, validating, or updating the stock discovery workflow CSV schema and handoff contracts between stock workflow skills.
---

# Stock Workflow Schema

Use this skill to keep all stock discovery skills aligned on the same row shape.

## References

Read `references/output_columns.md` when creating or validating the final CSV column order.

## Handoff Contract

Each skill receives and returns an array of row objects. Skills may add fields but should not remove source fields unless explicitly asked.

## Required Final Fields

Every final row should include:
- `Symbol`
- `Company`
- `Price`
- `Change(%)`
- `Catalyst Type`
- `Final Score`
- `Recommendation`
- `Confidence 1-5`
- `Next Research Step`
- `Data Quality Notes`
- `Run Timestamp`

