package fideslang

import (
	"testing"
)

func strPtr(s string) *string { return &s }

func buildTestTaxonomy() Taxonomy {
	return Taxonomy{
		DataCategory: []TaxonomyEntry{
			{FidesKey: "user", ParentKey: nil},
			{FidesKey: "user.contact", ParentKey: strPtr("user")},
			{FidesKey: "user.contact.email", ParentKey: strPtr("user.contact")},
			{FidesKey: "user.financial", ParentKey: strPtr("user")},
			{FidesKey: "user.financial.bank_account", ParentKey: strPtr("user.financial")},
			{FidesKey: "system", ParentKey: nil},
			{FidesKey: "system.operations", ParentKey: strPtr("system")},
		},
		DataUse: []TaxonomyEntry{
			{FidesKey: "marketing", ParentKey: nil},
			{FidesKey: "marketing.advertising", ParentKey: strPtr("marketing")},
			{FidesKey: "analytics", ParentKey: nil},
			{FidesKey: "essential", ParentKey: nil},
			{FidesKey: "essential.service", ParentKey: strPtr("essential")},
		},
		DataSubject: []TaxonomyEntry{
			{FidesKey: "customer", ParentKey: nil},
			{FidesKey: "employee", ParentKey: nil},
		},
	}
}

func TestEvaluate_PASS_NoViolation(t *testing.T) {
	req := &EvaluateRequest{
		Taxonomy: buildTestTaxonomy(),
		PolicyRule: PolicyRule{
			Name: "block-marketing-email",
			DataCategories: PolicyRuleTarget{
				Values:  []string{"user.financial"},
				Matches: MatchAny,
			},
			DataUses: PolicyRuleTarget{
				Values:  []string{"marketing"},
				Matches: MatchAny,
			},
			DataSubjects: PolicyRuleTarget{
				Values:  []string{"customer"},
				Matches: MatchAny,
			},
		},
		PrivacyDeclaration: PrivacyDeclaration{
			DataCategories: []string{"user.contact.email"},
			DataUse:        "essential.service",
			DataSubjects:   []string{"customer"},
		},
	}

	resp := Evaluate(req)

	if resp.Status != "PASS" {
		t.Errorf("expected PASS, got %s", resp.Status)
	}
	if len(resp.Violations) != 0 {
		t.Errorf("expected 0 violations, got %d", len(resp.Violations))
	}
}

func TestEvaluate_FAIL_AllDimensionsMatch(t *testing.T) {
	req := &EvaluateRequest{
		Taxonomy: buildTestTaxonomy(),
		PolicyRule: PolicyRule{
			Name: "block-marketing-pii",
			DataCategories: PolicyRuleTarget{
				Values:  []string{"user"},
				Matches: MatchAny,
			},
			DataUses: PolicyRuleTarget{
				Values:  []string{"marketing"},
				Matches: MatchAny,
			},
			DataSubjects: PolicyRuleTarget{
				Values:  []string{"customer"},
				Matches: MatchAny,
			},
		},
		PrivacyDeclaration: PrivacyDeclaration{
			DataCategories: []string{"user.contact.email"},
			DataUse:        "marketing.advertising",
			DataSubjects:   []string{"customer"},
		},
	}

	resp := Evaluate(req)

	if resp.Status != "FAIL" {
		t.Errorf("expected FAIL, got %s", resp.Status)
	}
	if len(resp.Violations) != 1 {
		t.Fatalf("expected 1 violation, got %d", len(resp.Violations))
	}
}

func TestEvaluate_PASS_UseMismatch(t *testing.T) {
	// Rule targets marketing, but declaration uses essential — no violation
	req := &EvaluateRequest{
		Taxonomy: buildTestTaxonomy(),
		PolicyRule: PolicyRule{
			Name: "block-marketing-user-data",
			DataCategories: PolicyRuleTarget{
				Values:  []string{"user"},
				Matches: MatchAny,
			},
			DataUses: PolicyRuleTarget{
				Values:  []string{"marketing"},
				Matches: MatchAny,
			},
			DataSubjects: PolicyRuleTarget{
				Values:  []string{"customer"},
				Matches: MatchAny,
			},
		},
		PrivacyDeclaration: PrivacyDeclaration{
			DataCategories: []string{"user.contact.email"},
			DataUse:        "essential.service",
			DataSubjects:   []string{"customer"},
		},
	}

	resp := Evaluate(req)

	if resp.Status != "PASS" {
		t.Errorf("expected PASS, got %s", resp.Status)
	}
}

func TestHierarchyMatching_ParentMatchesChild(t *testing.T) {
	tax := buildTestTaxonomy()
	idx := NewTaxonomyIndex(&tax)

	// "user" should match "user.contact.email" via hierarchy
	h := idx.GetCategoryHierarchy("user.contact.email")
	if len(h) != 3 {
		t.Fatalf("expected hierarchy of length 3, got %d: %v", len(h), h)
	}
	if h[0] != "user.contact.email" || h[1] != "user.contact" || h[2] != "user" {
		t.Errorf("unexpected hierarchy: %v", h)
	}
}

func TestMatchMode_ALL(t *testing.T) {
	// ALL: violation only if every declared type is covered
	tax := buildTestTaxonomy()
	idx := NewTaxonomyIndex(&tax)

	rule := &PolicyRule{
		Name: "test-all",
		DataCategories: PolicyRuleTarget{
			Values:  []string{"user"},
			Matches: MatchAll,
		},
		DataUses: PolicyRuleTarget{
			Values:  []string{"marketing"},
			Matches: MatchAny,
		},
		DataSubjects: PolicyRuleTarget{
			Values:  []string{"customer"},
			Matches: MatchAny,
		},
	}

	// Both categories are under "user" → ALL matched → violation
	decl := &PrivacyDeclaration{
		DataCategories: []string{"user.contact.email", "user.financial.bank_account"},
		DataUse:        "marketing.advertising",
		DataSubjects:   []string{"customer"},
	}

	violations := EvaluatePolicyRule(idx, rule, decl)
	if len(violations) == 0 {
		t.Error("expected violation when ALL categories match")
	}

	// Mix of user + system → not ALL user → no category violation → PASS
	decl2 := &PrivacyDeclaration{
		DataCategories: []string{"user.contact.email", "system.operations"},
		DataUse:        "marketing.advertising",
		DataSubjects:   []string{"customer"},
	}

	violations2 := EvaluatePolicyRule(idx, rule, decl2)
	if len(violations2) != 0 {
		t.Error("expected no violation when not ALL categories match")
	}
}

func TestMatchMode_NONE(t *testing.T) {
	tax := buildTestTaxonomy()
	idx := NewTaxonomyIndex(&tax)

	rule := &PolicyRule{
		Name: "test-none",
		DataCategories: PolicyRuleTarget{
			Values:  []string{"user.financial"},
			Matches: MatchNone,
		},
		DataUses: PolicyRuleTarget{
			Values:  []string{"marketing"},
			Matches: MatchAny,
		},
		DataSubjects: PolicyRuleTarget{
			Values:  []string{"customer"},
			Matches: MatchAny,
		},
	}

	// No financial data → NONE matches (violation because no overlap is the problem)
	decl := &PrivacyDeclaration{
		DataCategories: []string{"user.contact.email"},
		DataUse:        "marketing.advertising",
		DataSubjects:   []string{"customer"},
	}

	violations := EvaluatePolicyRule(idx, rule, decl)
	if len(violations) == 0 {
		t.Error("expected violation when NONE mode has no matches")
	}
}

func TestMatchMode_OTHER(t *testing.T) {
	tax := buildTestTaxonomy()
	idx := NewTaxonomyIndex(&tax)

	rule := &PolicyRule{
		Name: "test-other",
		DataCategories: PolicyRuleTarget{
			Values:  []string{"user.contact"},
			Matches: MatchOther,
		},
		DataUses: PolicyRuleTarget{
			Values:  []string{"marketing"},
			Matches: MatchAny,
		},
		DataSubjects: PolicyRuleTarget{
			Values:  []string{"customer"},
			Matches: MatchAny,
		},
	}

	// system.operations is NOT under user.contact → OTHER catches it
	decl := &PrivacyDeclaration{
		DataCategories: []string{"user.contact.email", "system.operations"},
		DataUse:        "marketing.advertising",
		DataSubjects:   []string{"customer"},
	}

	violations := EvaluatePolicyRule(idx, rule, decl)
	if len(violations) == 0 {
		t.Error("expected violation when OTHER mode finds non-matching types")
	}
}
