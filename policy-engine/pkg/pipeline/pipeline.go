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
type TableRef struct {
	Collection    string
	QualifiedName string
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
	Consumers map[string]fixtures.Consumer
	// Purposes maps purpose fides_key to the full Purpose entity.
	Purposes map[string]fixtures.Purpose
	// Datasets bundles per-dataset purposes + the table-name index.
	Datasets fixtures.Datasets
	// Policies is the enabled access policy list, in load order.
	Policies []pbac.AccessPolicy
}

// Input is one pipeline invocation: which identity, which tables, and
// optional runtime context (consent / geo / data_flows) used by unless
// conditions. QueryID and QueryText are echoed back in the record
// unchanged so callers can correlate results to source SQL.
type Input struct {
	QueryID   string
	Identity  string
	QueryText string
	Tables    []TableRef
	Context   map[string]interface{}
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
	datasetKeys, collections, unresolvedGaps := resolveTables(in.Tables, f.Datasets.Tables)

	// 3. Engine inputs
	consumerPurposes := buildConsumerPurposes(in.Identity, consumer, hasConsumer)
	datasetPurposes := buildDatasetPurposes(datasetKeys, f.Datasets.Purposes)

	// 4. Purpose evaluation (pass the collection list so collection-level
	//    purposes are picked up).
	purposeResult := pbac.EvaluatePurpose(consumerPurposes, datasetPurposes, collections)

	// 5. Gap reclassification: consumer found but no purposes declared
	gaps := append([]pbac.EvaluationGap{}, purposeResult.Gaps...)
	gaps = append(gaps, unresolvedGaps...)
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
		DatasetKeys:   datasetKeys,
		IsCompliant:   compliant,
		Violations:    violations,
		Gaps:          gaps,
		TotalAccesses: purposeResult.TotalAccesses,
		QueryText:     in.QueryText,
	}
}

// ── Private helpers ────────────────────────────────────────────────

// resolveTables walks the input tables and produces:
//   - dataset keys (deduplicated, in first-seen order)
//   - a per-dataset collection list for EvaluatePurpose to pick up
//     collection-level purpose overlap
//   - UNCONFIGURED_DATASET gaps for any table the index didn't resolve
func resolveTables(
	tables []TableRef,
	tableIndex map[string]string,
) ([]string, map[string][]string, []pbac.EvaluationGap) {
	seenKey := map[string]bool{}
	keys := []string{}
	collections := map[string][]string{}
	seenCollection := map[string]bool{} // dataset|collection
	gaps := []pbac.EvaluationGap{}

	for _, t := range tables {
		coll := strings.ToLower(t.Collection)
		if key, ok := tableIndex[coll]; ok {
			if !seenKey[key] {
				seenKey[key] = true
				keys = append(keys, key)
			}
			marker := key + "|" + coll
			if !seenCollection[marker] {
				seenCollection[marker] = true
				collections[key] = append(collections[key], coll)
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
	return keys, collections, gaps
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
) []pbac.PurposeViolation {
	out := make([]pbac.PurposeViolation, 0, len(violations))
	for _, v := range violations {
		dataUses := dataUsesForDatasetPurposes(v.DatasetPurposes, purposeIndex)
		req := &pbac.AccessEvaluationRequest{
			Identity:         identity,
			ConsumerID:       v.ConsumerID,
			ConsumerName:     v.ConsumerName,
			ConsumerPurposes: v.ConsumerPurposes,
			DatasetKey:       v.DatasetKey,
			DatasetPurposes:  v.DatasetPurposes,
			Collection:       v.Collection,
			DataUses:         dataUses,
			Context:          context,
		}
		result := pbac.EvaluatePolicies(policies, req)
		if result.Decision == pbac.PolicyAllow && result.DecisivePolicyKey != nil {
			key := *result.DecisivePolicyKey
			v.SuppressedByPolicy = &key
			if result.Action != nil {
				v.SuppressedByAction = result.Action
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

func allSuppressed(violations []pbac.PurposeViolation) bool {
	for _, v := range violations {
		if v.SuppressedByPolicy == nil {
			return false
		}
	}
	return true
}
