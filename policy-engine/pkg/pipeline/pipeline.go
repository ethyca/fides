// Package pipeline runs the full PBAC evaluation pipeline over a
// pre-loaded fixture set — identity resolution, dataset resolution,
// purpose evaluation, gap reclassification, and access-policy filtering.
//
// This is the "Option B" entry point: callers hand in fixture data
// (from YAML or otherwise), an identity, and a list of table references
// extracted from a SQL statement, and get back a single EvaluationRecord
// mirroring the service-layer record in fides/service/pbac/types.py.
//
// The pipeline does not parse SQL — that stays in Python (sqlglot).
// It also does not load fixtures itself — the fixtures package does
// that. Keeping those concerns separate means the same Go function
// can serve a CLI (Python calls it via the sidecar), a sidecar batch
// endpoint, and in-process Go callers.
package pipeline

import (
	"sort"
	"strings"

	"github.com/ethyca/fides/policy-engine/pkg/fixtures"
	"github.com/ethyca/fides/policy-engine/pkg/pbac"
)

// TableRef is a (collection, qualified_name) pair extracted from SQL.
// QualifiedName is used as the identifier on UNCONFIGURED_DATASET gaps
// when Collection does not resolve to a known dataset.
// Schema is the SQL schema (BQ dataset, Snowflake schema) used to
// disambiguate collections that share the same name across datasets.
// Columns holds the column names accessed from this table (extracted
// by the Python SQL parser). An empty list means SELECT * or parse
// failure — the pipeline falls back to all field categories.
type TableRef struct {
	Collection    string   `json:"collection"`
	Schema        string   `json:"schema,omitempty"`
	QualifiedName string   `json:"qualified_name,omitempty"`
	Columns       []string `json:"columns,omitempty"`
}

// EvaluationRecord is the per-statement result. Mirrors
// fides.service.pbac.types.EvaluationRecord with two deliberate deltas:
//   - Consumer is a name string, not the full DataConsumerEntity
//   - no timestamp (SQL text has no inherent time)
type EvaluationRecord struct {
	QueryID       string                  `json:"query_id"`
	Identity      string                  `json:"identity"`
	Consumer      *string                 `json:"consumer,omitempty"`
	DatasetKeys   []string                `json:"dataset_keys"`
	IsCompliant   bool                    `json:"is_compliant"`
	Violations    []pbac.PurposeViolation `json:"violations"`
	Gaps          []pbac.EvaluationGap    `json:"gaps"`
	TotalAccesses int                     `json:"total_accesses"`
	QueryText     string                  `json:"query_text,omitempty"`
}

// Fixtures bundles the four fixture collections the pipeline consumes.
// It mirrors what fixtures.Load*() returns, but decouples pipeline from
// the filesystem (callers can build Fixtures in-memory for tests or
// from any other source).
type Fixtures struct {
	// Consumers maps member identity (e.g. email) to its owning consumer.
	Consumers map[string]fixtures.Consumer `json:"consumers"`
	// Purposes maps purpose fides_key to the full Purpose entity.
	Purposes map[string]fixtures.Purpose `json:"purposes"`
	// Datasets bundles per-dataset purposes + the table-name index.
	Datasets fixtures.Datasets `json:"datasets"`
	// Policies is the enabled access policy list, in load order.
	Policies []pbac.AccessPolicy `json:"policies"`
}

// Input is one pipeline invocation: which identity, which tables, and
// optional runtime context (consent / geo / data_flows) used by unless
// conditions. QueryID and QueryText are echoed back in the record
// unchanged so callers can correlate results to source SQL.
type Input struct {
	QueryID   string                 `json:"query_id,omitempty"`
	Identity  string                 `json:"identity"`
	QueryText string                 `json:"query_text,omitempty"`
	Tables    []TableRef             `json:"tables"`
	Context   map[string]interface{} `json:"context,omitempty"`
}

// Evaluate runs the full PBAC pipeline for a single statement.
//
// Steps:
//  1. Resolve identity -> consumer via Fixtures.Consumers.
//  2. Resolve each TableRef.Collection -> dataset_key via the dataset
//     table index. Unknown tables become UNCONFIGURED_DATASET gaps
//     identified by QualifiedName.
//  3. Build the engine-facing ConsumerPurposes and DatasetPurposes.
//  4. Call pbac.EvaluatePurpose for the overlap check.
//  5. Reclassify UNRESOLVED_IDENTITY -> UNCONFIGURED_CONSUMER when the
//     consumer exists but declared no purposes.
//  6. For each purpose violation, resolve data_use via Fixtures.Purposes,
//     then run the violation through pbac.EvaluatePolicies. An ALLOW
//     suppresses the violation in place via SuppressedByPolicy /
//     SuppressedByAction — the violation stays in the record for audit.
//
// A record is compliant when every violation is suppressed and no gaps
// were recorded.
func Evaluate(f Fixtures, in Input) EvaluationRecord {
	// 1. Identity -> consumer
	consumer, hasConsumer := f.Consumers[in.Identity]

	// 2. Tables -> dataset_keys + per-dataset collection list + unresolved gaps
	resolved := resolveTables(in.Tables, f.Datasets.Tables)

	// 3. Engine inputs
	consumerPurposes := buildConsumerPurposes(in.Identity, consumer, hasConsumer)
	datasetPurposes := buildDatasetPurposes(resolved.DatasetKeys, f.Datasets.Purposes)

	// 4. Purpose evaluation (pass the collection list so collection-level
	//    purposes are picked up).
	purposeResult := pbac.EvaluatePurpose(consumerPurposes, datasetPurposes, resolved.Collections)

	// 5. Gap reclassification: consumer found but no purposes declared
	gaps := append([]pbac.EvaluationGap{}, purposeResult.Gaps...)
	gaps = append(gaps, resolved.Gaps...)
	if hasConsumer && len(consumer.Purposes) == 0 {
		for i, g := range gaps {
			if g.GapType == pbac.GapUnresolvedIdentity {
				gaps[i] = pbac.EvaluationGap{
					GapType:    pbac.GapUnconfiguredConsumer,
					Identifier: g.Identifier,
					DatasetKey: g.DatasetKey,
					Reason:     "Consumer has no declared purposes",
				}
			}
		}
	}

	// 6. Policy filtering — suppress in place, don't drop
	violations := filterViolationsThroughPolicies(
		purposeResult.Violations,
		f.Policies,
		f.Purposes,
		in.Identity,
		in.Context,
		resolved.Columns,
		f.Datasets.FieldCategories,
	)

	compliant := len(gaps) == 0 && allSuppressed(violations)

	var consumerRef *string
	if hasConsumer {
		name := consumer.Name
		consumerRef = &name
	}

	return EvaluationRecord{
		QueryID:       in.QueryID,
		Identity:      in.Identity,
		Consumer:      consumerRef,
		DatasetKeys:   resolved.DatasetKeys,
		IsCompliant:   compliant,
		Violations:    violations,
		Gaps:          gaps,
		TotalAccesses: purposeResult.TotalAccesses,
		QueryText:     in.QueryText,
	}
}

// ── Private helpers ────────────────────────────────────────────────

// resolveTablesResult holds everything produced by resolveTables.
type resolveTablesResult struct {
	DatasetKeys []string
	Collections map[string][]string
	Columns     map[string]map[string][]string // dataset_key -> collection -> columns
	Gaps        []pbac.EvaluationGap
}

// resolveTables walks the input tables and produces:
//   - dataset keys (deduplicated, in first-seen order)
//   - a per-dataset collection list for EvaluatePurpose to pick up
//     collection-level purpose overlap
//   - per-dataset-collection column lists for data category resolution
//   - UNCONFIGURED_DATASET gaps for any table the index didn't resolve
func resolveTables(
	tables []TableRef,
	tableIndex map[string]string,
) resolveTablesResult {
	seenKey := map[string]bool{}
	keys := []string{}
	collections := map[string][]string{}
	columns := map[string]map[string][]string{}
	seenCollection := map[string]bool{} // dataset|collection
	gaps := []pbac.EvaluationGap{}

	for _, t := range tables {
		coll := strings.ToLower(t.Collection)
		// Try schema-qualified lookup first to disambiguate collections
		// that share the same name across datasets (e.g. two datasets
		// both having a "transactions" collection).
		key, ok := "", false
		if t.Schema != "" {
			key, ok = tableIndex[strings.ToLower(t.Schema)+"."+coll]
		}
		if !ok {
			key, ok = tableIndex[coll]
		}
		if ok {
			if !seenKey[key] {
				seenKey[key] = true
				keys = append(keys, key)
			}
			marker := key + "|" + coll
			if !seenCollection[marker] {
				seenCollection[marker] = true
				collections[key] = append(collections[key], coll)
			}
			if len(t.Columns) > 0 {
				if columns[key] == nil {
					columns[key] = map[string][]string{}
				}
				columns[key][coll] = append(columns[key][coll], t.Columns...)
			}
			continue
		}
		identifier := t.QualifiedName
		if identifier == "" {
			identifier = t.Collection
		}
		gaps = append(gaps, pbac.EvaluationGap{
			GapType:    pbac.GapUnconfiguredDataset,
			Identifier: identifier,
			Reason:     "Dataset is not registered",
		})
	}
	return resolveTablesResult{
		DatasetKeys: keys,
		Collections: collections,
		Columns:     columns,
		Gaps:        gaps,
	}
}

func buildConsumerPurposes(
	identity string,
	consumer fixtures.Consumer,
	found bool,
) pbac.ConsumerPurposes {
	if !found {
		return pbac.ConsumerPurposes{
			ConsumerID:   identity,
			ConsumerName: identity,
			PurposeKeys:  nil,
		}
	}
	return pbac.ConsumerPurposes{
		ConsumerID:   consumer.Name,
		ConsumerName: consumer.Name,
		PurposeKeys:  append([]string{}, consumer.Purposes...),
	}
}

func buildDatasetPurposes(
	datasetKeys []string,
	purposeMap map[string]pbac.DatasetPurposes,
) map[string]pbac.DatasetPurposes {
	out := map[string]pbac.DatasetPurposes{}
	for _, key := range datasetKeys {
		if dp, ok := purposeMap[key]; ok {
			out[key] = dp
		} else {
			out[key] = pbac.DatasetPurposes{DatasetKey: key}
		}
	}
	return out
}

// filterViolationsThroughPolicies suppresses (but does not drop)
// violations that an ALLOW policy matches. Matches the Python
// SidecarPBACEvaluationService behavior: ALLOW -> SuppressedByPolicy,
// DENY/NO_DECISION -> violation stands unchanged.
func filterViolationsThroughPolicies(
	violations []pbac.PurposeViolation,
	policies []pbac.AccessPolicy,
	purposeIndex map[string]fixtures.Purpose,
	identity string,
	context map[string]interface{},
	columnsByDataset map[string]map[string][]string,
	fieldCategories map[string]map[string][]string,
) []pbac.PurposeViolation {
	out := make([]pbac.PurposeViolation, 0, len(violations))
	for _, v := range violations {
		dataUses := dataUsesForDatasetPurposes(v.DatasetPurposes, purposeIndex)

		// Enrich the violation with data_use (first resolved use from
		// the dataset's purposes), matching the Python service layer's
		// _resolve_data_uses step.
		if len(dataUses) > 0 {
			du := dataUses[0]
			v.DataUse = &du
		}

		var collection string
		if v.Collection != nil {
			collection = *v.Collection
		}
		dataCategories := resolveDataCategories(
			v.DatasetKey, collection,
			columnsByDataset, fieldCategories,
		)

		req := &pbac.AccessEvaluationRequest{
			Identity:         identity,
			ConsumerID:       v.ConsumerID,
			ConsumerName:     v.ConsumerName,
			ConsumerPurposes: v.ConsumerPurposes,
			DatasetKey:       v.DatasetKey,
			DatasetPurposes:  v.DatasetPurposes,
			Collection:       v.Collection,
			DataUses:         dataUses,
			DataCategories:   dataCategories,
			Context:          context,
		}
		result := pbac.EvaluatePolicies(policies, req)
		if result.Decision == pbac.PolicyAllow && result.DecisivePolicyKey != nil {
			key := *result.DecisivePolicyKey
			v.SuppressedByPolicy = &key
			// EvaluatePolicies deliberately only returns Action on
			// DENY decisions, so look up the decisive ALLOW policy's
			// action and control ourselves for auditability.
			for _, p := range policies {
				if p.Key == key {
					if p.Action != nil {
						action := *p.Action
						v.SuppressedByAction = &action
					}
					if p.Control != "" {
						ctrl := p.Control
						v.Control = &ctrl
					}
					break
				}
			}
		}
		out = append(out, v)
	}
	return out
}

// dataUsesForDatasetPurposes maps a set of dataset purpose keys to the
// data_use strings those purposes declare. Deterministic order.
func dataUsesForDatasetPurposes(
	datasetPurposes []string,
	purposeIndex map[string]fixtures.Purpose,
) []string {
	set := map[string]bool{}
	for _, pk := range datasetPurposes {
		if p, ok := purposeIndex[pk]; ok && p.DataUse != "" {
			set[p.DataUse] = true
		}
	}
	out := make([]string, 0, len(set))
	for u := range set {
		out = append(out, u)
	}
	sort.Strings(out)
	return out
}

// resolveDataCategories looks up data categories for the columns accessed
// in a specific dataset collection. If no specific columns were extracted
// (SELECT * or parse failure), returns all categories from all fields in
// the collection.
func resolveDataCategories(
	datasetKey string,
	collection string,
	columnsByDataset map[string]map[string][]string,
	fieldCategories map[string]map[string][]string,
) []string {
	if fieldCategories == nil || collection == "" {
		return nil
	}

	// Try schema-qualified lookup first for disambiguation
	qualified := strings.ToLower(datasetKey) + "." + collection
	collFields, ok := fieldCategories[qualified]
	if !ok {
		collFields, ok = fieldCategories[collection]
	}
	if !ok || len(collFields) == 0 {
		return nil
	}

	var columns []string
	if dsCols, ok := columnsByDataset[datasetKey]; ok {
		columns = dsCols[collection]
	}

	catSet := map[string]bool{}

	if len(columns) == 0 {
		// SELECT * or no columns extracted — use all field categories
		for _, cats := range collFields {
			for _, c := range cats {
				catSet[c] = true
			}
		}
	} else {
		for _, col := range columns {
			if cats, ok := collFields[col]; ok {
				for _, c := range cats {
					catSet[c] = true
				}
			}
		}
	}

	if len(catSet) == 0 {
		return nil
	}

	out := make([]string, 0, len(catSet))
	for c := range catSet {
		out = append(out, c)
	}
	sort.Strings(out)
	return out
}

// resolveDataCategories looks up data categories for the columns accessed
// in a specific dataset collection. If no specific columns were extracted
// (SELECT * or parse failure), returns all categories from all fields in
// the collection.
func resolveDataCategories(
	datasetKey string,
	collection string,
	columnsByDataset map[string]map[string][]string,
	fieldCategories map[string]map[string][]string,
) []string {
	if fieldCategories == nil || collection == "" {
		return nil
	}

	collFields, ok := fieldCategories[collection]
	if !ok || len(collFields) == 0 {
		return nil
	}

	var columns []string
	if dsCols, ok := columnsByDataset[datasetKey]; ok {
		columns = dsCols[collection]
	}

	catSet := map[string]bool{}

	if len(columns) == 0 {
		// SELECT * or no columns extracted — use all field categories
		for _, cats := range collFields {
			for _, c := range cats {
				catSet[c] = true
			}
		}
	} else {
		for _, col := range columns {
			if cats, ok := collFields[col]; ok {
				for _, c := range cats {
					catSet[c] = true
				}
			}
		}
	}

	if len(catSet) == 0 {
		return nil
	}

	out := make([]string, 0, len(catSet))
	for c := range catSet {
		out = append(out, c)
	}
	sort.Strings(out)
	return out
}

func allSuppressed(violations []pbac.PurposeViolation) bool {
	for _, v := range violations {
		if v.SuppressedByPolicy == nil {
			return false
		}
	}
	return true
}
