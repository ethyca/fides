package pbac

import (
	"sort"
	"strings"
)

// EvaluatePolicies evaluates a list of access policies against a request.
//
// Algorithm (from IMPLEMENTATION_GUIDE.md):
//  1. Sort enabled policies by priority (highest first)
//  2. For each policy, check if the match block applies to the request
//  3. If matched, evaluate unless conditions
//  4. Unless triggered + ALLOW → DENY (decisive, stop)
//  5. Unless triggered + DENY → SUPPRESSED (not decisive, continue)
//  6. Unless not triggered → decision stands as-is (decisive, stop)
//  7. No policy matched → NO_DECISION
func EvaluatePolicies(policies []AccessPolicy, request *AccessEvaluationRequest) *PolicyEvaluationResult {
	// Filter to enabled policies and sort by priority descending
	enabled := make([]AccessPolicy, 0, len(policies))
	for _, p := range policies {
		if p.Enabled {
			enabled = append(enabled, p)
		}
	}
	sort.Slice(enabled, func(i, j int) bool {
		return enabled[i].Priority > enabled[j].Priority
	})

	evaluated := make([]EvaluatedPolicyInfo, 0)

	for _, policy := range enabled {
		if !matchesRequest(&policy.Match, request) {
			continue
		}

		unlessTriggered := evaluateUnless(policy.Unless, request)

		if unlessTriggered {
			if policy.Decision == PolicyAllow {
				// ALLOW inverted to DENY — decisive, stop
				key := policy.Key
				priority := policy.Priority
				return &PolicyEvaluationResult{
					Decision:               PolicyDeny,
					DecisivePolicyKey:      &key,
					DecisivePolicyPriority: &priority,
					UnlessTriggered:        true,
					Action:                 policy.Action,
					EvaluatedPolicies:      evaluated,
				}
			}
			// DENY suppressed — not decisive, continue
			evaluated = append(evaluated, EvaluatedPolicyInfo{
				PolicyKey:       policy.Key,
				Priority:        policy.Priority,
				Matched:         true,
				Result:          "SUPPRESSED",
				UnlessTriggered: true,
			})
			continue
		}

		// Decision stands as-is — decisive, stop
		key := policy.Key
		priority := policy.Priority
		var action *PolicyAction
		if policy.Decision == PolicyDeny {
			action = policy.Action
		}
		return &PolicyEvaluationResult{
			Decision:               policy.Decision,
			DecisivePolicyKey:      &key,
			DecisivePolicyPriority: &priority,
			UnlessTriggered:        false,
			Action:                 action,
			EvaluatedPolicies:      evaluated,
		}
	}

	// No policy matched
	return &PolicyEvaluationResult{
		Decision:          PolicyNoDecision,
		EvaluatedPolicies: evaluated,
	}
}

// matchesRequest checks if a policy's match block applies to the request.
// An empty match block matches everything (catch-all policy).
func matchesRequest(match *MatchBlock, req *AccessEvaluationRequest) bool {
	if match.DataUse != nil && !matchesDimension(match.DataUse, req.DataUses) {
		return false
	}
	if match.DataCategory != nil && !matchesDimension(match.DataCategory, req.DataCategories) {
		return false
	}
	if match.DataSubject != nil && !matchesDimension(match.DataSubject, req.DataSubjects) {
		return false
	}
	return true
}

// matchesDimension checks if request values satisfy a match dimension's any/all operators.
// Uses taxonomy prefix matching: "user.contact" matches "user.contact.email".
func matchesDimension(dim *MatchDimension, requestValues []string) bool {
	// "any" — at least one match value must appear in request values
	if len(dim.Any) > 0 {
		found := false
		for _, matchVal := range dim.Any {
			if taxonomyMatchesAny(matchVal, requestValues) {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}

	// "all" — every match value must appear in request values
	if len(dim.All) > 0 {
		for _, matchVal := range dim.All {
			if !taxonomyMatchesAny(matchVal, requestValues) {
				return false
			}
		}
	}

	return true
}

// taxonomyMatchesAny checks if a taxonomy key matches any of the request values.
// A match key "user.contact" matches request value "user.contact.email" because
// it's a parent in the taxonomy hierarchy (prefix match).
func taxonomyMatchesAny(matchKey string, requestValues []string) bool {
	for _, reqVal := range requestValues {
		if taxonomyMatch(matchKey, reqVal) {
			return true
		}
	}
	return false
}

// taxonomyMatch checks if matchKey is equal to or a parent of requestValue.
// "user.contact" matches "user.contact.email" (prefix + dot boundary).
// "user.contact" matches "user.contact" (exact match).
// "user" does NOT match "user_data" (must be a dot boundary).
func taxonomyMatch(matchKey, requestValue string) bool {
	if matchKey == requestValue {
		return true
	}
	return strings.HasPrefix(requestValue, matchKey+".")
}

// evaluateUnless evaluates all unless conditions. All must trigger (AND logic)
// for the unless block to fire.
func evaluateUnless(constraints []Constraint, req *AccessEvaluationRequest) bool {
	if len(constraints) == 0 {
		return false
	}

	for _, c := range constraints {
		if !evaluateConstraint(&c, req) {
			return false
		}
	}
	return true
}

// evaluateConstraint evaluates a single unless condition against the request context.
func evaluateConstraint(c *Constraint, req *AccessEvaluationRequest) bool {
	switch c.Type {
	case ConstraintConsent:
		return evaluateConsentConstraint(c, req)
	case ConstraintGeoLocation:
		return evaluateGeoConstraint(c, req)
	case ConstraintDataFlow:
		return evaluateDataFlowConstraint(c, req)
	default:
		return false
	}
}

// evaluateConsentConstraint checks a consent-based unless condition.
// Looks up consent status in request.Context["consent"][privacy_notice_key].
func evaluateConsentConstraint(c *Constraint, req *AccessEvaluationRequest) bool {
	if req.Context == nil {
		return false
	}

	consentMap, ok := req.Context["consent"].(map[string]interface{})
	if !ok {
		return false
	}

	status, ok := consentMap[c.PrivacyNoticeKey].(string)
	if !ok {
		return false
	}

	switch c.Requirement {
	case "opt_in":
		return status == "opt_in"
	case "opt_out":
		return status == "opt_out"
	case "not_opt_in":
		return status != "opt_in"
	case "not_opt_out":
		return status != "opt_out"
	default:
		return false
	}
}

// evaluateGeoConstraint checks a geo_location-based unless condition.
// Resolves the field path in request.Context and checks against values.
func evaluateGeoConstraint(c *Constraint, req *AccessEvaluationRequest) bool {
	if req.Context == nil {
		return false
	}

	value := resolveContextField(req.Context, c.Field)
	if value == "" {
		return false
	}

	valueSet := make(map[string]bool, len(c.Values))
	for _, v := range c.Values {
		valueSet[v] = true
	}

	switch c.Operator {
	case "in":
		return valueSet[value]
	case "not_in":
		return !valueSet[value]
	default:
		return false
	}
}

// evaluateDataFlowConstraint checks a data_flow-based unless condition.
// Looks up system data flows in request.Context["data_flows"][direction].
func evaluateDataFlowConstraint(c *Constraint, req *AccessEvaluationRequest) bool {
	if req.Context == nil {
		return false
	}

	flowsMap, ok := req.Context["data_flows"].(map[string]interface{})
	if !ok {
		return false
	}

	directionFlows, ok := flowsMap[c.Direction].([]interface{})
	if !ok {
		return false
	}

	systemSet := make(map[string]bool, len(directionFlows))
	for _, s := range directionFlows {
		if str, ok := s.(string); ok {
			systemSet[str] = true
		}
	}

	switch c.Operator {
	case "any_of":
		for _, sys := range c.Systems {
			if systemSet[sys] {
				return true
			}
		}
		return false
	case "none_of":
		for _, sys := range c.Systems {
			if systemSet[sys] {
				return false
			}
		}
		return true
	default:
		return false
	}
}

// resolveContextField traverses a dotted field path in the context map.
// e.g. "environment.geo_location" → context["environment"]["geo_location"]
func resolveContextField(ctx map[string]interface{}, field string) string {
	parts := strings.Split(field, ".")
	var current interface{} = ctx

	for _, part := range parts {
		m, ok := current.(map[string]interface{})
		if !ok {
			return ""
		}
		current = m[part]
	}

	if str, ok := current.(string); ok {
		return str
	}
	return ""
}
