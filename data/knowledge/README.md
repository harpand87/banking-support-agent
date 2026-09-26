# Approved Knowledge Corpus

The canonical approved synthetic corpus is `approved_knowledge.jsonl` in this directory. Its exact schema, validation rules, metadata, and update procedure are documented in [Data Specifications](../../docs/data-specification.md). `app/knowledge.py` loads this file; it no longer hardcodes the records.

Use one UTF-8 JSON object per line, preserve unique `KB-*` source IDs, and keep every loaded record marked `approved` and `synthetic: true`. Never add real customer records, identity documents, account details, or secrets.
