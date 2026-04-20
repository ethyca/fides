// Package pbac implements purpose-based access control evaluation.
//
// It mirrors the Python evaluation engine in fides/service/pbac/ and is the
// canonical Go implementation of the PBAC purpose-overlap algorithm.
package pbac

import (
	"fmt"
	"sort"
	"strings"
)

// GapType classifies PBAC coverage gaps.
type GapType string

const (
	GapUnresolvedIdentity  GapType = "unresolved_identity"
	GapUnconfiguredDataset GapType = "unconfigured_dataset"
	// GapUnconfiguredConsumer ("unconfigured_consumer") is produced by the
	// Python service layer (step 5) when reclassifying identity gaps for
	// consumers that exist but have no purposes. The Go engine does not
	// produce this gap type — it's a service-layer concern, not an engine
	// concern.
)

// ConsumerPurposes holds the declared purposes for a data consumer.
type ConsumerPurposes struct {
	ConsumerID   string   `json:"consumer_id"`
	ConsumerName string   `json:"consumer_name"`
	PurposeKeys  []string `json:"purpose_keys"`
}

// DatasetPurposes holds the declared purposes for a dataset, including
// per-collection purposes. Purpose inheritance is additive: a collection's
// effective purposes are purpose_keys | collection_purposes[collection].
type DatasetPurposes struct {
	DatasetKey         string              `json:"dataset_key"`
	PurposeKeys        []string            `json:"purpose_keys"`
	CollectionPurposes map[string][]string `json:"collection_purposes,omitempty"`
}

// EffectivePurposes returns the effective purposes for a collection (additive
// inheritance). If collection is empty, returns dataset-level purposes only.
func (d *DatasetPurposes) EffectivePurposes(collection string) map[string]bool {
	result := make(map[string]bool, len(d.PurposeKeys))
	for _, k := range d.PurposeKeys {
		result[k] = true
	}
	if collection != "" {
		if cp, ok := d.CollectionPurposes[collection]; ok {
			for _, k := range cp {
				result[k] = true
			}
		}
	}
	return result
}

// PurposeViolation represents a purpose-based access violation.
type PurposeViolation struct {
	ConsumerID       string   `json:"consumer_id"`
	ConsumerName     string   `json:"consumer_name"`
	DatasetKey       string   `json:"dataset_key"`
	Collection       *string  `json:"collection,omitempty"`
	ConsumerPurposes []string `json:"consumer_purposes"`
	DatasetPurposes  []string `json:"dataset_purposes"`
	Reason           string   `json:"reason"`
	DataUse          *string  `json:"data_use,omitempty"`
	Control          *string  `json:"control,omitempty"`
}

// EvaluationGap represents a gap in PBAC coverage — incomplete configuration,
// not a policy violation.
type EvaluationGap struct {
	GapType    GapType `json:"gap_type"`
	Identifier string  `json:"identifier"`
	DatasetKey *string `json:"dataset_key,omitempty"`
	Reason     string  `json:"reason"`
}

// PurposeEvaluationResult is the output from EvaluatePurpose.
type PurposeEvaluationResult struct {
	Violations    []PurposeViolation `json:"violations"`
	Gaps          []EvaluationGap    `json:"gaps"`
	TotalAccesses int                `json:"total_accesses"`
}

// EvaluatePurposeRequest is the JSON request body used by the fidesplus
// sidecar HTTP handler for POST /v1/evaluate-purpose.
type EvaluatePurposeRequest struct {
	Consumer    ConsumerPurposes           `json:"consumer"`
	Datasets    map[string]DatasetPurposes `json:"datasets"`
	Collections map[string][]string        `json:"collections,omitempty"`
}

// Helper: sorted keys from a set for deterministic output.
func sortedKeys(m map[string]bool) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}

// Helper: build a set from a slice.
func toSet(s []string) map[string]bool {
	m := make(map[string]bool, len(s))
	for _, v := range s {
		m[v] = true
	}
	return m
}

// Helper: check if two sets intersect.
func intersects(a, b map[string]bool) bool {
	// iterate the smaller set
	if len(a) > len(b) {
		a, b = b, a
	}
	for k := range a {
		if b[k] {
			return true
		}
	}
	return false
}

// violationReason builds a human-readable reason string matching the Python format.
func violationReason(consumerPurposes, datasetPurposes map[string]bool) string {
	cp := sortedKeys(consumerPurposes)
	dp := sortedKeys(datasetPurposes)
	return fmt.Sprintf(
		"Consumer purposes [%s] do not overlap with dataset purposes [%s]",
		strings.Join(cp, ", "),
		strings.Join(dp, ", "),
	)
}
