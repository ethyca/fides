package pbac

import (
	"testing"
)

func strPtr(s string) *string { return &s }

func TestRule1_NoConsumerPurposes_ProducesGap(t *testing.T) {
	consumer := ConsumerPurposes{
		ConsumerID:   "consumer-1",
		ConsumerName: "test-consumer",
		PurposeKeys:  []string{},
	}
	datasets := map[string]DatasetPurposes{
		"ds_billing": {
			DatasetKey:  "ds_billing",
			PurposeKeys: []string{"billing"},
		},
	}

	result := EvaluatePurpose(consumer, datasets, nil)

	if len(result.Violations) != 0 {
		t.Errorf("expected 0 violations, got %d", len(result.Violations))
	}
	if len(result.Gaps) != 1 {
		t.Fatalf("expected 1 gap, got %d", len(result.Gaps))
	}
	if result.Gaps[0].GapType != GapUnresolvedIdentity {
		t.Errorf("expected gap type %s, got %s", GapUnresolvedIdentity, result.Gaps[0].GapType)
	}
	if result.TotalAccesses != 1 {
		t.Errorf("expected 1 total access, got %d", result.TotalAccesses)
	}
}

func TestRule2_NoOverlap_ProducesViolation(t *testing.T) {
	consumer := ConsumerPurposes{
		ConsumerID:   "consumer-1",
		ConsumerName: "Analytics Pipeline",
		PurposeKeys:  []string{"analytics"},
	}
	datasets := map[string]DatasetPurposes{
		"billing_db": {
			DatasetKey:  "billing_db",
			PurposeKeys: []string{"billing"},
		},
	}

	result := EvaluatePurpose(consumer, datasets, nil)

	if len(result.Violations) != 1 {
		t.Fatalf("expected 1 violation, got %d", len(result.Violations))
	}
	v := result.Violations[0]
	if v.ConsumerID != "consumer-1" {
		t.Errorf("expected consumer_id 'consumer-1', got '%s'", v.ConsumerID)
	}
	if v.DatasetKey != "billing_db" {
		t.Errorf("expected dataset_key 'billing_db', got '%s'", v.DatasetKey)
	}
	if len(result.Gaps) != 0 {
		t.Errorf("expected 0 gaps, got %d", len(result.Gaps))
	}
}

func TestRule2_Overlap_Compliant(t *testing.T) {
	consumer := ConsumerPurposes{
		ConsumerID:   "consumer-1",
		ConsumerName: "Billing Pipeline",
		PurposeKeys:  []string{"billing", "analytics"},
	}
	datasets := map[string]DatasetPurposes{
		"billing_db": {
			DatasetKey:  "billing_db",
			PurposeKeys: []string{"billing"},
		},
	}

	result := EvaluatePurpose(consumer, datasets, nil)

	if len(result.Violations) != 0 {
		t.Errorf("expected 0 violations, got %d", len(result.Violations))
	}
	if len(result.Gaps) != 0 {
		t.Errorf("expected 0 gaps, got %d", len(result.Gaps))
	}
	if result.TotalAccesses != 1 {
		t.Errorf("expected 1 total access, got %d", result.TotalAccesses)
	}
}

func TestRule3_NoDatasetPurposes_ProducesGap(t *testing.T) {
	consumer := ConsumerPurposes{
		ConsumerID:   "consumer-1",
		ConsumerName: "test-consumer",
		PurposeKeys:  []string{"analytics"},
	}
	datasets := map[string]DatasetPurposes{
		"unknown_db": {
			DatasetKey:  "unknown_db",
			PurposeKeys: []string{},
		},
	}

	result := EvaluatePurpose(consumer, datasets, nil)

	if len(result.Violations) != 0 {
		t.Errorf("expected 0 violations, got %d", len(result.Violations))
	}
	if len(result.Gaps) != 1 {
		t.Fatalf("expected 1 gap, got %d", len(result.Gaps))
	}
	if result.Gaps[0].GapType != GapUnconfiguredDataset {
		t.Errorf("expected gap type %s, got %s", GapUnconfiguredDataset, result.Gaps[0].GapType)
	}
}

func TestCollectionPurposes_AdditiveInheritance(t *testing.T) {
	consumer := ConsumerPurposes{
		ConsumerID:   "consumer-1",
		ConsumerName: "Billing Pipeline",
		PurposeKeys:  []string{"accounting"},
	}
	datasets := map[string]DatasetPurposes{
		"billing_db": {
			DatasetKey:  "billing_db",
			PurposeKeys: []string{"billing"},
			CollectionPurposes: map[string][]string{
				"invoices": {"accounting"},
			},
		},
	}
	collections := map[string][]string{
		"billing_db": {"invoices"},
	}

	result := EvaluatePurpose(consumer, datasets, collections)

	// "accounting" is in invoices collection purposes, which is unioned
	// with dataset "billing" purposes. Consumer has "accounting" which
	// overlaps with effective {"billing", "accounting"} → compliant.
	if len(result.Violations) != 0 {
		t.Errorf("expected 0 violations, got %d", len(result.Violations))
	}
	if len(result.Gaps) != 0 {
		t.Errorf("expected 0 gaps, got %d", len(result.Gaps))
	}
}

func TestCollectionPurposes_NoOverlap_Violation(t *testing.T) {
	consumer := ConsumerPurposes{
		ConsumerID:   "consumer-1",
		ConsumerName: "Marketing Pipeline",
		PurposeKeys:  []string{"marketing"},
	}
	datasets := map[string]DatasetPurposes{
		"billing_db": {
			DatasetKey:  "billing_db",
			PurposeKeys: []string{"billing"},
			CollectionPurposes: map[string][]string{
				"invoices": {"accounting"},
			},
		},
	}
	collections := map[string][]string{
		"billing_db": {"invoices"},
	}

	result := EvaluatePurpose(consumer, datasets, collections)

	if len(result.Violations) != 1 {
		t.Fatalf("expected 1 violation, got %d", len(result.Violations))
	}
	if result.Violations[0].Collection == nil || *result.Violations[0].Collection != "invoices" {
		t.Errorf("expected collection 'invoices'")
	}
}

func TestMultipleDatasets_MixedResults(t *testing.T) {
	consumer := ConsumerPurposes{
		ConsumerID:   "consumer-1",
		ConsumerName: "Analytics",
		PurposeKeys:  []string{"analytics"},
	}
	datasets := map[string]DatasetPurposes{
		"analytics_db": {
			DatasetKey:  "analytics_db",
			PurposeKeys: []string{"analytics"},
		},
		"billing_db": {
			DatasetKey:  "billing_db",
			PurposeKeys: []string{"billing"},
		},
		"unknown_db": {
			DatasetKey:  "unknown_db",
			PurposeKeys: []string{},
		},
	}

	result := EvaluatePurpose(consumer, datasets, nil)

	if len(result.Violations) != 1 {
		t.Errorf("expected 1 violation, got %d", len(result.Violations))
	}
	if len(result.Gaps) != 1 {
		t.Errorf("expected 1 gap, got %d", len(result.Gaps))
	}
	if result.TotalAccesses != 3 {
		t.Errorf("expected 3 total accesses, got %d", result.TotalAccesses)
	}
}
