# Catalog snapshot

Read-only copies of the Hub store's `gear/*` and `meta/*` documents, pulled from the live
artifact database on 2026-09-13. They exist so scripts under `import/` can validate ids, types
and colour tokens without network access. The live store is the source of truth; refresh these
by reading the artifact database again, never by editing here.
