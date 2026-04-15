// Package sqlextract pulls table references out of SQL text with regex.
//
// This is a deliberately simple extractor intended for the standalone
// fides-pbac CLI, where platform audit APIs (BigQuery Jobs, Snowflake
// ACCESS_HISTORY, Databricks query history) aren't available to hand
// back structured table references.
//
// Known limitations:
//   - Views are not expanded (a query against a view reports the view
//     name, not the underlying tables).
//   - Wildcard tables (BigQuery `events_*`) are returned verbatim.
//   - Tables referenced inside UDFs or stored procedures are missed.
//   - Old-style comma joins (FROM a, b, c) only pick up the first table.
//   - Identifiers with inner dots inside a single quoted span
//     ("schema.table" as one name) are treated as two parts.
//
// For exact resolution, use the platform's native audit API. Use this
// extractor when you only have raw SQL text and need a best-effort answer.
package sqlextract

import (
	"regexp"
	"strings"
)

// TableRef references a table in an external data platform.
//
// Catalog maps to a BigQuery project, Snowflake database, or Databricks
// catalog. Schema maps to a BQ dataset, Snowflake schema, or Databricks
// schema. Table is the table name.
type TableRef struct {
	Catalog string `json:"catalog"`
	Schema  string `json:"schema"`
	Table   string `json:"table"`
}

// QualifiedName returns the dot-separated identifier, skipping empty parts.
func (t TableRef) QualifiedName() string {
	parts := make([]string, 0, 3)
	if t.Catalog != "" {
		parts = append(parts, t.Catalog)
	}
	if t.Schema != "" {
		parts = append(parts, t.Schema)
	}
	if t.Table != "" {
		parts = append(parts, t.Table)
	}
	return strings.Join(parts, ".")
}

var (
	// Strip /* ... */ block comments. (?s) makes . match newlines.
	// Nested comments are rare enough that we don't handle them.
	blockCommentRe = regexp.MustCompile(`(?s)/\*.*?\*/`)

	// Strip -- line comments through end of line.
	lineCommentRe = regexp.MustCompile(`--[^\n]*`)

	// Match FROM/JOIN followed by a 1-3 part identifier. Each part may
	// optionally be wrapped in backticks or double quotes. A `(`
	// following FROM/JOIN (subquery) doesn't match because it's not a
	// word character.
	tableRe = regexp.MustCompile(
		"(?i)\\b(?:FROM|JOIN)\\s+" +
			"([`\"]?\\w+[`\"]?" +
			"(?:\\s*\\.\\s*[`\"]?\\w+[`\"]?){0,2})",
	)

	// Collect CTE names from WITH clauses: `WITH name AS (` or `, name AS (`.
	// These are filtered from the results since they aren't real tables.
	cteRe = regexp.MustCompile(`(?is)(?:WITH|,)\s+([a-zA-Z_]\w*)\s+AS\s*\(`)
)

// StripComments returns the SQL with /* */ and -- comments removed.
// Lines that become empty after stripping are dropped, and leading and
// trailing whitespace is trimmed. Internal whitespace is otherwise
// preserved so multi-line queries keep their shape.
func StripComments(sql string) string {
	s := blockCommentRe.ReplaceAllString(sql, " ")
	s = lineCommentRe.ReplaceAllString(s, "")
	lines := strings.Split(s, "\n")
	kept := lines[:0]
	for _, l := range lines {
		if strings.TrimSpace(l) != "" {
			kept = append(kept, l)
		}
	}
	return strings.TrimSpace(strings.Join(kept, "\n"))
}

// Extract returns the distinct list of table references found in a SQL
// string, in the order they first appear.
//
// Comments are stripped before extraction. CTE names declared in WITH
// clauses are filtered out.
func Extract(sql string) []TableRef {
	stripped := blockCommentRe.ReplaceAllString(sql, " ")
	stripped = lineCommentRe.ReplaceAllString(stripped, "")

	ctes := collectCTENames(stripped)

	seen := make(map[string]bool)
	refs := make([]TableRef, 0)
	for _, m := range tableRe.FindAllStringSubmatch(stripped, -1) {
		ref := parseIdentifier(m[1])
		if ref.Table == "" {
			continue
		}
		// Skip unqualified CTE references.
		if ref.Schema == "" && ref.Catalog == "" &&
			ctes[strings.ToLower(ref.Table)] {
			continue
		}
		key := strings.ToLower(ref.QualifiedName())
		if seen[key] {
			continue
		}
		seen[key] = true
		refs = append(refs, ref)
	}
	return refs
}

func collectCTENames(sql string) map[string]bool {
	ctes := make(map[string]bool)
	for _, m := range cteRe.FindAllStringSubmatch(sql, -1) {
		ctes[strings.ToLower(m[1])] = true
	}
	return ctes
}

// parseIdentifier splits a 1-3 part identifier into a TableRef.
// Strips surrounding backticks and double quotes from each part.
func parseIdentifier(s string) TableRef {
	parts := strings.Split(s, ".")
	cleaned := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		p = strings.Trim(p, "`\"")
		if p != "" {
			cleaned = append(cleaned, p)
		}
	}
	switch len(cleaned) {
	case 1:
		return TableRef{Table: cleaned[0]}
	case 2:
		return TableRef{Schema: cleaned[0], Table: cleaned[1]}
	case 3:
		return TableRef{Catalog: cleaned[0], Schema: cleaned[1], Table: cleaned[2]}
	default:
		return TableRef{}
	}
}
