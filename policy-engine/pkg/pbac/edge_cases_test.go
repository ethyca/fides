package pbac

import (
	"testing"
)

// ── Purpose evaluation edge cases ────────────────────────────────────

func TestPurpose_EmptyDatasets_ZeroAccesses(t *testing.T) {
	consumer := ConsumerPurposes{
		ConsumerID: "c1", ConsumerName: "Test", PurposeKeys: []string{"billing"},
	}
	result := EvaluatePurpose(consumer, map[string]DatasetPurposes{}, nil)

	if result.TotalAccesses != 0 {
		t.Errorf("expected 0 accesses, got %d", result.TotalAccesses)
	}
	if len(result.Violations) != 0 {
		t.Errorf("expected 0 violations, got %d", len(result.Violations))
	}
	if len(result.Gaps) != 0 {
		t.Errorf("expected 0 gaps, got %d", len(result.Gaps))
	}
}

func TestPurpose_NilCollections_NoPanic(t *testing.T) {
	consumer := ConsumerPurposes{
		ConsumerID: "c1", ConsumerName: "Test", PurposeKeys: []string{"billing"},
	}
	datasets := map[string]DatasetPurposes{
		"db1": {DatasetKey: "db1", PurposeKeys: []string{"billing"}},
	}

	// Should not panic with nil collections
	result := EvaluatePurpose(consumer, datasets, nil)
	if result.TotalAccesses != 1 {
		t.Errorf("expected 1 access, got %d", result.TotalAccesses)
	}
}

func TestPurpose_MultipleCollections_CountedSeparately(t *testing.T) {
	consumer := ConsumerPurposes{
		ConsumerID: "c1", ConsumerName: "Test", PurposeKeys: []string{"billing"},
	}
	datasets := map[string]DatasetPurposes{
		"db1": {
			DatasetKey:  "db1",
			PurposeKeys: []string{"billing"},
			CollectionPurposes: map[string][]string{
				"invoices": {"billing"},
				"payments": {"billing"},
			},
		},
	}
	collections := map[string][]string{
		"db1": {"invoices", "payments"},
	}

	result := EvaluatePurpose(consumer, datasets, collections)

	if result.TotalAccesses != 2 {
		t.Errorf("expected 2 accesses (one per collection), got %d", result.TotalAccesses)
	}
}

func TestPurpose_DuplicatePurposeKeys_StillWorks(t *testing.T) {
	consumer := ConsumerPurposes{
		ConsumerID: "c1", ConsumerName: "Test",
		PurposeKeys: []string{"billing", "billing", "analytics"},
	}
	datasets := map[string]DatasetPurposes{
		"db1": {DatasetKey: "db1", PurposeKeys: []string{"billing"}},
	}

	result := EvaluatePurpose(consumer, datasets, nil)

	// Should still be compliant
	if len(result.Violations) != 0 {
		t.Errorf("expected 0 violations, got %d", len(result.Violations))
	}
}

func TestPurpose_EmptyCollectionPurposes_InheritsDatasetOnly(t *testing.T) {
	consumer := ConsumerPurposes{
		ConsumerID: "c1", ConsumerName: "Test", PurposeKeys: []string{"billing"},
	}
	datasets := map[string]DatasetPurposes{
		"db1": {
			DatasetKey:         "db1",
			PurposeKeys:        []string{"billing"},
			CollectionPurposes: map[string][]string{},
		},
	}
	collections := map[string][]string{
		"db1": {"unknown_collection"},
	}

	result := EvaluatePurpose(consumer, datasets, collections)

	// Collection has no extra purposes, but dataset-level "billing" still applies
	if len(result.Violations) != 0 {
		t.Errorf("expected 0 violations (dataset purpose inherited), got %d", len(result.Violations))
	}
}

func TestPurpose_ViolationsHaveSortedPurposes(t *testing.T) {
	consumer := ConsumerPurposes{
		ConsumerID: "c1", ConsumerName: "Test",
		PurposeKeys: []string{"z_purpose", "a_purpose"},
	}
	datasets := map[string]DatasetPurposes{
		"db1": {DatasetKey: "db1", PurposeKeys: []string{"other"}},
	}

	result := EvaluatePurpose(consumer, datasets, nil)

	if len(result.Violations) != 1 {
		t.Fatalf("expected 1 violation, got %d", len(result.Violations))
	}

	// Purposes should be sorted in the violation for deterministic output
	cp := result.Violations[0].ConsumerPurposes
	if len(cp) != 2 || cp[0] != "a_purpose" || cp[1] != "z_purpose" {
		t.Errorf("expected sorted consumer purposes [a_purpose, z_purpose], got %v", cp)
	}
}

func TestPurpose_GapsAndViolationsNeverNil(t *testing.T) {
	consumer := ConsumerPurposes{
		ConsumerID: "c1", ConsumerName: "Test", PurposeKeys: []string{"billing"},
	}
	datasets := map[string]DatasetPurposes{
		"db1": {DatasetKey: "db1", PurposeKeys: []string{"billing"}},
	}

	result := EvaluatePurpose(consumer, datasets, nil)

	// Slices should be empty, not nil (for clean JSON serialization)
	if result.Violations == nil {
		t.Error("violations should be empty slice, not nil")
	}
	if result.Gaps == nil {
		t.Error("gaps should be empty slice, not nil")
	}
}

// ── EffectivePurposes edge cases ─────────────────────────────────────

func TestEffectivePurposes_EmptyCollection_ReturnsDatasetOnly(t *testing.T) {
	ds := DatasetPurposes{
		DatasetKey:  "db1",
		PurposeKeys: []string{"billing"},
	}

	effective := ds.EffectivePurposes("")
	if len(effective) != 1 || !effective["billing"] {
		t.Errorf("expected {billing}, got %v", effective)
	}
}

func TestEffectivePurposes_UnknownCollection_ReturnsDatasetOnly(t *testing.T) {
	ds := DatasetPurposes{
		DatasetKey:  "db1",
		PurposeKeys: []string{"billing"},
		CollectionPurposes: map[string][]string{
			"invoices": {"accounting"},
		},
	}

	effective := ds.EffectivePurposes("nonexistent")
	if len(effective) != 1 || !effective["billing"] {
		t.Errorf("expected {billing}, got %v", effective)
	}
}

func TestEffectivePurposes_Additive(t *testing.T) {
	ds := DatasetPurposes{
		DatasetKey:  "db1",
		PurposeKeys: []string{"billing"},
		CollectionPurposes: map[string][]string{
			"invoices": {"accounting", "reporting"},
		},
	}

	effective := ds.EffectivePurposes("invoices")
	if len(effective) != 3 {
		t.Errorf("expected 3 effective purposes, got %d: %v", len(effective), effective)
	}
	for _, key := range []string{"billing", "accounting", "reporting"} {
		if !effective[key] {
			t.Errorf("expected %s in effective purposes", key)
		}
	}
}

// ── Policy evaluation edge cases ─────────────────────────────────────

func TestPolicy_EmptyPoliciesList(t *testing.T) {
	result := EvaluatePolicies(nil, &AccessEvaluationRequest{})
	if result.Decision != PolicyNoDecision {
		t.Errorf("expected NO_DECISION, got %s", result.Decision)
	}
	if result.EvaluatedPolicies == nil {
		t.Error("evaluated_policies should be empty slice, not nil")
	}
}

func TestPolicy_AllDisabled(t *testing.T) {
	policies := []AccessPolicy{
		{ID: "p1", Key: "disabled-1", Priority: 100, Enabled: false, Decision: PolicyDeny, Match: MatchBlock{}},
		{ID: "p2", Key: "disabled-2", Priority: 200, Enabled: false, Decision: PolicyAllow, Match: MatchBlock{}},
	}

	result := EvaluatePolicies(policies, &AccessEvaluationRequest{})
	if result.Decision != PolicyNoDecision {
		t.Errorf("expected NO_DECISION, got %s", result.Decision)
	}
}

func TestPolicy_NoMatchDimensions_CatchAll(t *testing.T) {
	// An empty MatchBlock should match any request, even with empty data_uses
	policies := []AccessPolicy{
		{ID: "p1", Key: "catch-all", Priority: 1, Enabled: true, Decision: PolicyDeny, Match: MatchBlock{}},
	}

	result := EvaluatePolicies(policies, &AccessEvaluationRequest{})
	if result.Decision != PolicyDeny {
		t.Errorf("expected DENY (catch-all), got %s", result.Decision)
	}
}

func TestPolicy_MatchAll_RequiresEveryValue(t *testing.T) {
	policies := []AccessPolicy{
		{
			ID: "p1", Key: "require-both", Priority: 100, Enabled: true,
			Decision: PolicyDeny,
			Match: MatchBlock{
				DataCategory: &MatchDimension{
					All: []string{"user.contact", "user.financial"},
				},
			},
		},
	}

	// Only one category → no match
	req1 := &AccessEvaluationRequest{
		DataCategories: []string{"user.contact.email"},
	}
	result1 := EvaluatePolicies(policies, req1)
	if result1.Decision != PolicyNoDecision {
		t.Errorf("expected NO_DECISION (only one category), got %s", result1.Decision)
	}

	// Both categories → match → DENY
	req2 := &AccessEvaluationRequest{
		DataCategories: []string{"user.contact.email", "user.financial.bank_account"},
	}
	result2 := EvaluatePolicies(policies, req2)
	if result2.Decision != PolicyDeny {
		t.Errorf("expected DENY (both categories), got %s", result2.Decision)
	}
}

func TestPolicy_MatchAnyAndAll_Combined(t *testing.T) {
	policies := []AccessPolicy{
		{
			ID: "p1", Key: "combined", Priority: 100, Enabled: true,
			Decision: PolicyDeny,
			Match: MatchBlock{
				DataUse: &MatchDimension{Any: []string{"marketing"}},
				DataCategory: &MatchDimension{All: []string{"user.contact", "user.financial"}},
			},
		},
	}

	// Marketing use + both categories → match
	req := &AccessEvaluationRequest{
		DataUses:       []string{"marketing.advertising"},
		DataCategories: []string{"user.contact.email", "user.financial.bank_account"},
	}
	result := EvaluatePolicies(policies, req)
	if result.Decision != PolicyDeny {
		t.Errorf("expected DENY, got %s", result.Decision)
	}

	// Marketing use + only one category → no match
	req2 := &AccessEvaluationRequest{
		DataUses:       []string{"marketing.advertising"},
		DataCategories: []string{"user.contact.email"},
	}
	result2 := EvaluatePolicies(policies, req2)
	if result2.Decision != PolicyNoDecision {
		t.Errorf("expected NO_DECISION, got %s", result2.Decision)
	}
}

func TestPolicy_UnlessNoContext_DoesNotTrigger(t *testing.T) {
	policies := []AccessPolicy{
		{
			ID: "p1", Key: "allow-unless", Priority: 100, Enabled: true,
			Decision: PolicyAllow,
			Match:    MatchBlock{},
			Unless: []Constraint{
				{Type: ConstraintConsent, PrivacyNoticeKey: "notice", Requirement: "opt_out"},
			},
		},
	}

	// No context → unless can't evaluate → doesn't trigger → ALLOW stands
	result := EvaluatePolicies(policies, &AccessEvaluationRequest{})
	if result.Decision != PolicyAllow {
		t.Errorf("expected ALLOW (no context), got %s", result.Decision)
	}
}

func TestPolicy_DenyAction_OnlyReturnedForDeny(t *testing.T) {
	policies := []AccessPolicy{
		{
			ID: "p1", Key: "allow-with-action", Priority: 100, Enabled: true,
			Decision: PolicyAllow,
			Match:    MatchBlock{},
			Action:   &PolicyAction{Message: "this should not appear"},
		},
	}

	result := EvaluatePolicies(policies, &AccessEvaluationRequest{})
	if result.Decision != PolicyAllow {
		t.Errorf("expected ALLOW, got %s", result.Decision)
	}
	if result.Action != nil {
		t.Error("action should be nil for ALLOW decisions")
	}
}

func TestPolicy_ResolveContextField_Nested(t *testing.T) {
	ctx := map[string]interface{}{
		"a": map[string]interface{}{
			"b": map[string]interface{}{
				"c": "deep_value",
			},
		},
	}

	val := resolveContextField(ctx, "a.b.c")
	if val != "deep_value" {
		t.Errorf("expected 'deep_value', got '%s'", val)
	}
}

func TestPolicy_ResolveContextField_MissingPath(t *testing.T) {
	ctx := map[string]interface{}{
		"a": map[string]interface{}{"b": "value"},
	}

	val := resolveContextField(ctx, "a.b.c.d")
	if val != "" {
		t.Errorf("expected empty string for missing path, got '%s'", val)
	}
}

func TestPolicy_ResolveContextField_NonStringValue(t *testing.T) {
	ctx := map[string]interface{}{
		"a": map[string]interface{}{"b": 42},
	}

	val := resolveContextField(ctx, "a.b")
	if val != "" {
		t.Errorf("expected empty string for non-string value, got '%s'", val)
	}
}
