package pbac

import (
	"testing"
)

func intPtr(i int) *int { return &i }

func basePolicies() []AccessPolicy {
	return []AccessPolicy{
		{
			ID: "p1", Key: "allow-marketing", Priority: 100, Enabled: true,
			Decision: PolicyAllow,
			Match: MatchBlock{
				DataUse: &MatchDimension{Any: []string{"marketing"}},
			},
		},
		{
			ID: "p2", Key: "deny-financial", Priority: 200, Enabled: true,
			Decision: PolicyDeny,
			Match: MatchBlock{
				DataCategory: &MatchDimension{Any: []string{"user.financial"}},
			},
			Action: &PolicyAction{Message: "Financial data access denied"},
		},
		{
			ID: "p3", Key: "catch-all-deny", Priority: 0, Enabled: true,
			Decision: PolicyDeny,
			Match:    MatchBlock{}, // empty = matches everything
			Action:   &PolicyAction{Message: "Default deny"},
		},
	}
}

func TestEvaluatePolicies_HighestPriorityWins(t *testing.T) {
	policies := basePolicies()
	req := &AccessEvaluationRequest{
		DataUses:       []string{"marketing.advertising"},
		DataCategories: []string{"user.financial.bank_account"},
	}

	result := EvaluatePolicies(policies, req)

	// Priority 200 (deny-financial) should win over 100 (allow-marketing)
	if result.Decision != PolicyDeny {
		t.Errorf("expected DENY, got %s", result.Decision)
	}
	if result.DecisivePolicyKey == nil || *result.DecisivePolicyKey != "deny-financial" {
		t.Errorf("expected decisive policy 'deny-financial'")
	}
}

func TestEvaluatePolicies_AllowWhenMatched(t *testing.T) {
	policies := basePolicies()
	req := &AccessEvaluationRequest{
		DataUses:       []string{"marketing.advertising"},
		DataCategories: []string{"user.contact.email"},
	}

	result := EvaluatePolicies(policies, req)

	// deny-financial doesn't match (no user.financial), allow-marketing matches
	if result.Decision != PolicyAllow {
		t.Errorf("expected ALLOW, got %s", result.Decision)
	}
	if result.DecisivePolicyKey == nil || *result.DecisivePolicyKey != "allow-marketing" {
		t.Errorf("expected decisive policy 'allow-marketing'")
	}
}

func TestEvaluatePolicies_CatchAllDeny(t *testing.T) {
	policies := basePolicies()
	req := &AccessEvaluationRequest{
		DataUses:       []string{"essential.service"},
		DataCategories: []string{"system.operations"},
	}

	result := EvaluatePolicies(policies, req)

	// Nothing specific matches, catch-all (priority 0) kicks in
	if result.Decision != PolicyDeny {
		t.Errorf("expected DENY, got %s", result.Decision)
	}
	if result.DecisivePolicyKey == nil || *result.DecisivePolicyKey != "catch-all-deny" {
		t.Errorf("expected decisive policy 'catch-all-deny'")
	}
}

func TestEvaluatePolicies_NoDecisionWhenNoPolicies(t *testing.T) {
	result := EvaluatePolicies([]AccessPolicy{}, &AccessEvaluationRequest{})

	if result.Decision != PolicyNoDecision {
		t.Errorf("expected NO_DECISION, got %s", result.Decision)
	}
}

func TestEvaluatePolicies_DisabledPoliciesSkipped(t *testing.T) {
	policies := []AccessPolicy{
		{
			ID: "p1", Key: "disabled", Priority: 100, Enabled: false,
			Decision: PolicyDeny,
			Match:    MatchBlock{},
		},
	}

	result := EvaluatePolicies(policies, &AccessEvaluationRequest{})

	if result.Decision != PolicyNoDecision {
		t.Errorf("expected NO_DECISION, got %s", result.Decision)
	}
}

// ── Unless condition tests ───────────────────────────────────────────

func TestUnless_ConsentOptOut_InvertsAllow(t *testing.T) {
	policies := []AccessPolicy{
		{
			ID: "p1", Key: "allow-unless-optout", Priority: 100, Enabled: true,
			Decision: PolicyAllow,
			Match: MatchBlock{
				DataUse: &MatchDimension{Any: []string{"marketing"}},
			},
			Unless: []Constraint{
				{
					Type:             ConstraintConsent,
					PrivacyNoticeKey: "do_not_sell",
					Requirement:      "opt_out",
				},
			},
			Action: &PolicyAction{Message: "User opted out"},
		},
	}

	req := &AccessEvaluationRequest{
		DataUses: []string{"marketing.advertising"},
		Context: map[string]interface{}{
			"consent": map[string]interface{}{
				"do_not_sell": "opt_out",
			},
		},
	}

	result := EvaluatePolicies(policies, req)

	// ALLOW + unless triggered → DENY
	if result.Decision != PolicyDeny {
		t.Errorf("expected DENY (inverted ALLOW), got %s", result.Decision)
	}
	if !result.UnlessTriggered {
		t.Error("expected unless_triggered=true")
	}
}

func TestUnless_ConsentNotTriggered_AllowStands(t *testing.T) {
	policies := []AccessPolicy{
		{
			ID: "p1", Key: "allow-unless-optout", Priority: 100, Enabled: true,
			Decision: PolicyAllow,
			Match: MatchBlock{
				DataUse: &MatchDimension{Any: []string{"marketing"}},
			},
			Unless: []Constraint{
				{
					Type:             ConstraintConsent,
					PrivacyNoticeKey: "do_not_sell",
					Requirement:      "opt_out",
				},
			},
		},
	}

	req := &AccessEvaluationRequest{
		DataUses: []string{"marketing.advertising"},
		Context: map[string]interface{}{
			"consent": map[string]interface{}{
				"do_not_sell": "opt_in", // NOT opt_out, so unless doesn't trigger
			},
		},
	}

	result := EvaluatePolicies(policies, req)

	if result.Decision != PolicyAllow {
		t.Errorf("expected ALLOW, got %s", result.Decision)
	}
	if result.UnlessTriggered {
		t.Error("expected unless_triggered=false")
	}
}

func TestUnless_DenySuppressed_ContinuesToNext(t *testing.T) {
	policies := []AccessPolicy{
		{
			ID: "p1", Key: "deny-unless-geo", Priority: 200, Enabled: true,
			Decision: PolicyDeny,
			Match:    MatchBlock{},
			Unless: []Constraint{
				{
					Type:     ConstraintGeoLocation,
					Field:    "environment.geo_location",
					Operator: "in",
					Values:   []string{"US-CA"},
				},
			},
		},
		{
			ID: "p2", Key: "fallback-allow", Priority: 100, Enabled: true,
			Decision: PolicyAllow,
			Match:    MatchBlock{},
		},
	}

	req := &AccessEvaluationRequest{
		Context: map[string]interface{}{
			"environment": map[string]interface{}{
				"geo_location": "US-CA",
			},
		},
	}

	result := EvaluatePolicies(policies, req)

	// DENY + unless triggered → SUPPRESSED, continue to fallback-allow
	if result.Decision != PolicyAllow {
		t.Errorf("expected ALLOW (fallback), got %s", result.Decision)
	}
	if result.DecisivePolicyKey == nil || *result.DecisivePolicyKey != "fallback-allow" {
		t.Errorf("expected decisive policy 'fallback-allow'")
	}
	// The suppressed policy should be in the audit trail
	if len(result.EvaluatedPolicies) != 1 {
		t.Fatalf("expected 1 evaluated policy (suppressed), got %d", len(result.EvaluatedPolicies))
	}
	if result.EvaluatedPolicies[0].Result != "SUPPRESSED" {
		t.Errorf("expected SUPPRESSED, got %s", result.EvaluatedPolicies[0].Result)
	}
}

func TestUnless_GeoNotIn(t *testing.T) {
	policies := []AccessPolicy{
		{
			ID: "p1", Key: "deny-outside-ca", Priority: 100, Enabled: true,
			Decision: PolicyDeny,
			Match:    MatchBlock{},
			Unless: []Constraint{
				{
					Type:     ConstraintGeoLocation,
					Field:    "environment.geo_location",
					Operator: "not_in",
					Values:   []string{"US-CA", "US-VA"},
				},
			},
		},
	}

	// User is in US-CA → not_in returns false → unless NOT triggered → DENY stands
	req := &AccessEvaluationRequest{
		Context: map[string]interface{}{
			"environment": map[string]interface{}{
				"geo_location": "US-CA",
			},
		},
	}

	result := EvaluatePolicies(policies, req)
	if result.Decision != PolicyDeny {
		t.Errorf("expected DENY, got %s", result.Decision)
	}

	// User is in EU-DE → not_in returns true → unless triggered → DENY suppressed
	req2 := &AccessEvaluationRequest{
		Context: map[string]interface{}{
			"environment": map[string]interface{}{
				"geo_location": "EU-DE",
			},
		},
	}

	result2 := EvaluatePolicies(policies, req2)
	if result2.Decision != PolicyNoDecision {
		t.Errorf("expected NO_DECISION (deny suppressed, no fallback), got %s", result2.Decision)
	}
}

func TestUnless_DataFlow(t *testing.T) {
	policies := []AccessPolicy{
		{
			ID: "p1", Key: "allow-unless-egress", Priority: 100, Enabled: true,
			Decision: PolicyAllow,
			Match:    MatchBlock{},
			Unless: []Constraint{
				{
					Type:      ConstraintDataFlow,
					Direction: "egress",
					Operator:  "any_of",
					Systems:   []string{"external_vendor"},
				},
			},
		},
	}

	// Egress to external_vendor → unless triggers → ALLOW inverted to DENY
	req := &AccessEvaluationRequest{
		Context: map[string]interface{}{
			"data_flows": map[string]interface{}{
				"egress": []interface{}{"external_vendor", "partner_api"},
			},
		},
	}

	result := EvaluatePolicies(policies, req)
	if result.Decision != PolicyDeny {
		t.Errorf("expected DENY (inverted), got %s", result.Decision)
	}
}

func TestUnless_MultipleConstraints_AllMustTrigger(t *testing.T) {
	policies := []AccessPolicy{
		{
			ID: "p1", Key: "allow-unless-both", Priority: 100, Enabled: true,
			Decision: PolicyAllow,
			Match:    MatchBlock{},
			Unless: []Constraint{
				{
					Type:             ConstraintConsent,
					PrivacyNoticeKey: "do_not_sell",
					Requirement:      "opt_out",
				},
				{
					Type:     ConstraintGeoLocation,
					Field:    "environment.geo_location",
					Operator: "in",
					Values:   []string{"US-CA"},
				},
			},
		},
	}

	// Only consent triggers, not geo → unless does NOT trigger → ALLOW stands
	req := &AccessEvaluationRequest{
		Context: map[string]interface{}{
			"consent": map[string]interface{}{
				"do_not_sell": "opt_out",
			},
			"environment": map[string]interface{}{
				"geo_location": "US-NY",
			},
		},
	}

	result := EvaluatePolicies(policies, req)
	if result.Decision != PolicyAllow {
		t.Errorf("expected ALLOW (only one constraint triggered), got %s", result.Decision)
	}

	// Both trigger → ALLOW inverted to DENY
	req2 := &AccessEvaluationRequest{
		Context: map[string]interface{}{
			"consent": map[string]interface{}{
				"do_not_sell": "opt_out",
			},
			"environment": map[string]interface{}{
				"geo_location": "US-CA",
			},
		},
	}

	result2 := EvaluatePolicies(policies, req2)
	if result2.Decision != PolicyDeny {
		t.Errorf("expected DENY (both constraints triggered), got %s", result2.Decision)
	}
}

// ── Taxonomy matching tests ──────────────────────────────────────────

func TestTaxonomyMatch_ExactMatch(t *testing.T) {
	if !taxonomyMatch("user.contact", "user.contact") {
		t.Error("expected exact match")
	}
}

func TestTaxonomyMatch_ParentMatchesChild(t *testing.T) {
	if !taxonomyMatch("user.contact", "user.contact.email") {
		t.Error("expected parent to match child")
	}
}

func TestTaxonomyMatch_ChildDoesNotMatchParent(t *testing.T) {
	if taxonomyMatch("user.contact.email", "user.contact") {
		t.Error("child should not match parent")
	}
}

func TestTaxonomyMatch_NoDotBoundaryFalsePositive(t *testing.T) {
	if taxonomyMatch("user", "user_data") {
		t.Error("should not match across non-dot boundary")
	}
}

func TestMatchDimension_Any(t *testing.T) {
	dim := &MatchDimension{Any: []string{"marketing", "analytics"}}
	if !matchesDimension(dim, []string{"marketing.advertising"}) {
		t.Error("expected any to match")
	}
	if matchesDimension(dim, []string{"essential.service"}) {
		t.Error("expected any to not match")
	}
}

func TestMatchDimension_All(t *testing.T) {
	dim := &MatchDimension{All: []string{"user.contact", "user.financial"}}

	// Both present
	if !matchesDimension(dim, []string{"user.contact.email", "user.financial.bank_account"}) {
		t.Error("expected all to match when both present")
	}

	// Only one present
	if matchesDimension(dim, []string{"user.contact.email"}) {
		t.Error("expected all to not match when one missing")
	}
}

func TestMatchBlock_EmptyMatchesEverything(t *testing.T) {
	match := &MatchBlock{}
	req := &AccessEvaluationRequest{
		DataUses:       []string{"marketing"},
		DataCategories: []string{"user.contact"},
		DataSubjects:   []string{"customer"},
	}
	if !matchesRequest(match, req) {
		t.Error("empty match block should match everything")
	}
}
