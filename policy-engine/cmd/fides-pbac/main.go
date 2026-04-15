// Command fides-pbac evaluates raw SQL queries against a PBAC config.
//
// Usage:
//
//	fides-pbac --config pbac/ --identity alice@demo.example pbac/entries/alice.txt
//	echo "SELECT * FROM prod.events.page_views" | \
//	    fides-pbac --config pbac/ --identity alice@demo.example
//
// A standalone Go binary with no server dependency: parses SQL, resolves
// datasets, evaluates purpose overlap, and filters violations through
// access policies.
//
// Output is JSON to stdout: one record per SQL statement.
package main

import (
	"crypto/rand"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"github.com/ethyca/fides/policy-engine/pkg/fixtures"
	"github.com/ethyca/fides/policy-engine/pkg/pbac"
	"github.com/ethyca/fides/policy-engine/pkg/sqlextract"
)

// record is the JSON output shape, one per SQL statement. Mirrors
// fides.service.pbac.types.EvaluationRecord, with one extension:
// PurposeViolation entries carry SuppressedByPolicy / SuppressedByAction
// when an ALLOW policy overrode the violation, so suppressions remain
// auditable. A record is compliant when no violation stands (every
// violation has a SuppressedByPolicy) and no gaps were recorded.
type record struct {
	QueryID       string                  `json:"query_id"`
	Identity      string                  `json:"identity"`
	Consumer      *string                 `json:"consumer"`
	DatasetKeys   []string                `json:"dataset_keys"`
	IsCompliant   bool                    `json:"is_compliant"`
	Violations    []pbac.PurposeViolation `json:"violations"`
	Gaps          []pbac.EvaluationGap    `json:"gaps"`
	TotalAccesses int                     `json:"total_accesses"`
	QueryText     string                  `json:"query_text"`
}

type output struct {
	Records []record `json:"records"`
}

func main() {
	var (
		configDir = flag.String("config", "",
			"Directory containing consumers/, purposes/, datasets/, policies/ YAML fixtures (required)")
		identity = flag.String("identity", "",
			"User identity to attribute every query in the input to (required)")
	)
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: %s --config DIR --identity EMAIL [FILE]\n\n", os.Args[0])
		fmt.Fprintln(os.Stderr, "Evaluate SQL queries against PBAC config. Reads SQL from FILE or stdin.")
		fmt.Fprintln(os.Stderr, "Each top-level statement (split on ;) becomes one EvaluationRecord.")
		fmt.Fprintln(os.Stderr)
		flag.PrintDefaults()
	}
	flag.Parse()

	if *configDir == "" || *identity == "" {
		flag.Usage()
		os.Exit(2)
	}

	consumers, err := fixtures.LoadConsumers(filepath.Join(*configDir, "consumers"))
	if err != nil {
		die(err)
	}
	purposes, err := fixtures.LoadPurposes(filepath.Join(*configDir, "purposes"))
	if err != nil {
		die(err)
	}
	datasets, err := fixtures.LoadDatasets(filepath.Join(*configDir, "datasets"))
	if err != nil {
		die(err)
	}
	policies, err := fixtures.LoadPolicies(filepath.Join(*configDir, "policies"))
	if err != nil {
		die(err)
	}

	sqlText, err := readInput(flag.Args())
	if err != nil {
		die(err)
	}

	statements := splitStatements(sqlText)
	records := make([]record, 0, len(statements))
	for _, stmt := range statements {
		records = append(records, evaluateStatement(stmt, *identity, consumers, purposes, datasets, policies))
	}

	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	if err := enc.Encode(output{Records: records}); err != nil {
		die(err)
	}
}

// evaluateStatement runs one SQL statement through the full pipeline:
// identity resolution → table extraction → dataset resolution → purpose
// evaluation → gap reclassification → policy filtering of violations.
func evaluateStatement(
	sql string,
	identity string,
	consumers map[string]fixtures.Consumer,
	purposes map[string]fixtures.Purpose,
	datasets fixtures.Datasets,
	policies []pbac.AccessPolicy,
) record {
	tables := sqlextract.Extract(sql)

	// Dataset resolution by table name. Assumes table names are unique
	// across all datasets. Tables not present in any dataset's
	// collections are keyed by their qualified name so the resulting
	// UNCONFIGURED_DATASET gap points at the specific unknown table.
	//
	// Each resolved table is also recorded as a collection access on
	// its owning dataset so the engine can apply collection- and
	// field-level purposes (via DatasetPurposes.CollectionPurposes).
	datasetKeys := make([]string, 0, len(tables))
	collections := map[string][]string{}
	for _, t := range tables {
		name := strings.ToLower(t.Table)
		if key, ok := datasets.Tables[name]; ok {
			datasetKeys = append(datasetKeys, key)
			collections[key] = append(collections[key], name)
		} else {
			datasetKeys = append(datasetKeys, t.QualifiedName())
		}
	}

	consumer, consumerFound := consumers[identity]
	var consumerPurposes pbac.ConsumerPurposes
	if consumerFound {
		consumerPurposes = pbac.ConsumerPurposes{
			ConsumerID:   consumer.Name,
			ConsumerName: consumer.Name,
			PurposeKeys:  consumer.Purposes,
		}
	} else {
		consumerPurposes = pbac.ConsumerPurposes{
			ConsumerID:   identity,
			ConsumerName: identity,
			PurposeKeys:  nil,
		}
	}

	dsMap := make(map[string]pbac.DatasetPurposes, len(datasetKeys))
	for _, key := range datasetKeys {
		if dp, ok := datasets.Purposes[key]; ok {
			dsMap[key] = dp
		} else {
			dsMap[key] = pbac.DatasetPurposes{DatasetKey: key, PurposeKeys: nil}
		}
	}

	result := pbac.EvaluatePurpose(consumerPurposes, dsMap, collections)

	// Gap reclassification: when the consumer was found but has no
	// declared purposes, the engine's UNRESOLVED_IDENTITY gaps are
	// reclassified to UNCONFIGURED_CONSUMER.
	if consumerFound && len(consumer.Purposes) == 0 {
		for i, g := range result.Gaps {
			if g.GapType == pbac.GapUnresolvedIdentity {
				result.Gaps[i] = pbac.EvaluationGap{
					GapType:    "unconfigured_consumer",
					Identifier: consumer.Name,
					DatasetKey: g.DatasetKey,
					Reason:     "Consumer has no declared purposes",
				}
			}
		}
	}

	violations := applyPolicySuppression(result.Violations, purposes, policies)

	var consumerName *string
	if consumerFound {
		name := consumer.Name
		consumerName = &name
	}

	return record{
		QueryID:       newQueryID(),
		Identity:      identity,
		Consumer:      consumerName,
		DatasetKeys:   datasetKeys,
		IsCompliant:   isCompliant(violations, result.Gaps),
		Violations:    violations,
		Gaps:          result.Gaps,
		TotalAccesses: result.TotalAccesses,
		QueryText:     sqlextract.StripComments(sql),
	}
}

// isCompliant is true when no violation is still standing (every
// violation has been suppressed by a policy) and no gaps were recorded.
func isCompliant(violations []pbac.PurposeViolation, gaps []pbac.EvaluationGap) bool {
	if len(gaps) > 0 {
		return false
	}
	for _, v := range violations {
		if v.SuppressedByPolicy == nil {
			return false
		}
	}
	return true
}

// applyPolicySuppression runs each purpose violation through the access
// policy evaluator. Violations the policy engine resolves to ALLOW are
// marked in-place with SuppressedByPolicy and (when present) the
// decisive policy's action. Non-suppressed violations are returned
// unchanged. The returned slice contains every input violation in
// input order.
//
// Populates AccessEvaluationRequest.DataUses by mapping each dataset
// purpose key through the loaded Purpose map to its data_use — this is
// how policy match blocks on data_use find data to match against.
func applyPolicySuppression(
	violations []pbac.PurposeViolation,
	purposes map[string]fixtures.Purpose,
	policies []pbac.AccessPolicy,
) []pbac.PurposeViolation {
	if len(violations) == 0 || len(policies) == 0 {
		return violations
	}

	out := make([]pbac.PurposeViolation, 0, len(violations))
	for _, v := range violations {
		req := pbac.AccessEvaluationRequest{
			ConsumerID:       v.ConsumerID,
			ConsumerName:     v.ConsumerName,
			ConsumerPurposes: v.ConsumerPurposes,
			DatasetKey:       v.DatasetKey,
			DatasetPurposes:  v.DatasetPurposes,
			Collection:       v.Collection,
			DataUses:         dataUsesForPurposes(v.DatasetPurposes, purposes),
		}
		res := pbac.EvaluatePolicies(policies, &req)
		if res != nil && res.Decision == pbac.PolicyAllow && res.DecisivePolicyKey != nil {
			key := *res.DecisivePolicyKey
			v.SuppressedByPolicy = &key
			if res.Action != nil {
				action := *res.Action
				v.SuppressedByAction = &action
			}
		}
		out = append(out, v)
	}
	return out
}

// dataUsesForPurposes maps purpose fides_keys to their data_use strings
// via the loaded Purpose map. Purposes with no configured data_use are
// skipped. Result is deduplicated while preserving input order.
func dataUsesForPurposes(purposeKeys []string, purposes map[string]fixtures.Purpose) []string {
	if len(purposeKeys) == 0 || len(purposes) == 0 {
		return nil
	}
	seen := map[string]bool{}
	out := make([]string, 0, len(purposeKeys))
	for _, pk := range purposeKeys {
		p, ok := purposes[pk]
		if !ok || p.DataUse == "" {
			continue
		}
		if seen[p.DataUse] {
			continue
		}
		seen[p.DataUse] = true
		out = append(out, p.DataUse)
	}
	return out
}

// readInput returns the SQL text from the first positional arg, or stdin
// if no arg (or "-") is given.
func readInput(args []string) (string, error) {
	if len(args) == 0 || args[0] == "-" {
		b, err := io.ReadAll(os.Stdin)
		if err != nil {
			return "", fmt.Errorf("read stdin: %w", err)
		}
		return string(b), nil
	}
	b, err := os.ReadFile(args[0])
	if err != nil {
		return "", fmt.Errorf("read %s: %w", args[0], err)
	}
	return string(b), nil
}

// splitStatements splits SQL on top-level semicolons, preserving the
// original text of each statement (including comments). Respects single-
// quoted strings and both SQL comment styles so semicolons inside them
// are not treated as separators.
//
// Known limitation: does not handle backslash-escaped quotes, doubled
// single quotes ('' = '), or dollar-quoted strings (Postgres). Good
// enough for the demo fixtures.
func splitStatements(sql string) []string {
	var stmts []string
	var buf strings.Builder
	var (
		inSingleQuote  bool
		inLineComment  bool
		inBlockComment bool
	)

	flush := func() {
		s := strings.TrimSpace(buf.String())
		if s != "" {
			stmts = append(stmts, s)
		}
		buf.Reset()
	}

	for i := 0; i < len(sql); i++ {
		c := sql[i]
		switch {
		case inLineComment:
			buf.WriteByte(c)
			if c == '\n' {
				inLineComment = false
			}
		case inBlockComment:
			buf.WriteByte(c)
			if c == '*' && i+1 < len(sql) && sql[i+1] == '/' {
				buf.WriteByte(sql[i+1])
				i++
				inBlockComment = false
			}
		case inSingleQuote:
			buf.WriteByte(c)
			if c == '\'' {
				inSingleQuote = false
			}
		case c == '-' && i+1 < len(sql) && sql[i+1] == '-':
			inLineComment = true
			buf.WriteByte(c)
		case c == '/' && i+1 < len(sql) && sql[i+1] == '*':
			inBlockComment = true
			buf.WriteByte(c)
			buf.WriteByte(sql[i+1])
			i++
		case c == '\'':
			inSingleQuote = true
			buf.WriteByte(c)
		case c == ';':
			flush()
		default:
			buf.WriteByte(c)
		}
	}
	flush()
	return stmts
}

// newQueryID returns a UUIDv4-formatted string using crypto/rand.
func newQueryID() string {
	b := make([]byte, 16)
	if _, err := rand.Read(b); err != nil {
		panic(fmt.Sprintf("crypto/rand: %v", err))
	}
	b[6] = (b[6] & 0x0f) | 0x40 // version 4
	b[8] = (b[8] & 0x3f) | 0x80 // variant 10
	return fmt.Sprintf("%x-%x-%x-%x-%x", b[0:4], b[4:6], b[6:8], b[8:10], b[10:])
}

func die(err error) {
	fmt.Fprintf(os.Stderr, "error: %v\n", err)
	os.Exit(1)
}
