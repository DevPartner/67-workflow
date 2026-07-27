
# MCP `sb` Tools

The sb (Second Brain) MCP server exposes three tools:

### `keyword_search` — use by default

Best for: exact names, document titles, code identifiers, filenames, acronyms, technical terms.

```json
{ "query": "Sitecore Send SeriesConfigurationService", "top_k": 5 }
```

### `semantic_search`

Best for: concepts, ideas, natural language questions, "where did I write about…".

```json
{ "query": "How I designed a real-time meeting transcription architecture", "top_k": 5 }
```

### `get_document`

Fetches the full content of a single document by ID. Use as a second call when a
search result contains a relevant ID and you need the complete note rather than the
snippet returned by search.

```json
{ "collection": null, "id": "858a40" }
```

- `collection` — optional; scope to a specific collection or pass `null` for all.
- `id` — the document ID returned by a prior `keyword_search` or `semantic_search`.

## sb MCP usage rules

- Always start with one `keyword_search` or `semantic_search` call.
- Optionally follow with one `get_document` call if the full document is needed.
- Maximum two sb tool calls per user request (search + optional get_document).
- Do not retry the same tool call with different parameters.
- Do not call `get_document` without a prior search result that provided the ID.
