// Package fideslang implements the Fideslang policy rule evaluation algorithm.
//
// It evaluates whether a privacy declaration violates a policy rule by matching
// data categories, data uses, and data subjects against the fideslang taxonomy
// hierarchy. This is the Go translation of the evaluation engine used in
// fides/src/fides/api/util/ and benchmarked in Adrian's sidecar POC.
package fideslang

// MatchMode represents the matching mode for policy rules.
type MatchMode string

const (
	MatchAny   MatchMode = "ANY"
	MatchAll   MatchMode = "ALL"
	MatchNone  MatchMode = "NONE"
	MatchOther MatchMode = "OTHER"
)

// PolicyRuleTarget represents a rule's constraint on a specific dimension
// (categories, uses, or subjects).
type PolicyRuleTarget struct {
	Values  []string  `json:"values"`
	Matches MatchMode `json:"matches"`
}

// PolicyRule represents a single rule within a policy.
type PolicyRule struct {
	Name           string           `json:"name"`
	DataCategories PolicyRuleTarget `json:"data_categories"`
	DataUses       PolicyRuleTarget `json:"data_uses"`
	DataSubjects   PolicyRuleTarget `json:"data_subjects"`
}

// PrivacyDeclaration represents a system's declaration of data usage.
type PrivacyDeclaration struct {
	DataCategories []string `json:"data_categories"`
	DataUse        string   `json:"data_use"`
	DataSubjects   []string `json:"data_subjects"`
}

// TaxonomyEntry represents a single entry in a taxonomy hierarchy.
type TaxonomyEntry struct {
	FidesKey  string  `json:"fides_key"`
	ParentKey *string `json:"parent_key,omitempty"`
}

// Taxonomy holds the taxonomy data for evaluation.
type Taxonomy struct {
	DataCategory []TaxonomyEntry `json:"data_category"`
	DataUse      []TaxonomyEntry `json:"data_use"`
	DataSubject  []TaxonomyEntry `json:"data_subject"`
}

// ViolatingAttributes captures the specific attributes that violated a rule.
type ViolatingAttributes struct {
	DataCategories []string `json:"data_categories"`
	DataUses       []string `json:"data_uses"`
	DataSubjects   []string `json:"data_subjects"`
}

// Violation represents a policy violation.
type Violation struct {
	Detail              string              `json:"detail"`
	ViolatingAttributes ViolatingAttributes `json:"violating_attributes"`
}

// EvaluateRequest is the input for policy evaluation.
type EvaluateRequest struct {
	Taxonomy           Taxonomy           `json:"taxonomy"`
	PolicyRule         PolicyRule         `json:"policy_rule"`
	PrivacyDeclaration PrivacyDeclaration `json:"privacy_declaration"`
}

// EvaluateResponse is the output of policy evaluation.
type EvaluateResponse struct {
	Status           string      `json:"status"` // "PASS" or "FAIL"
	Violations       []Violation `json:"violations"`
	EvaluationTimeUs int64       `json:"evaluation_time_us"`
}
