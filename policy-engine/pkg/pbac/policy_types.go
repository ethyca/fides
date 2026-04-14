package pbac

// PolicyDecision is the outcome of an access policy evaluation.
type PolicyDecision string

const (
	PolicyAllow      PolicyDecision = "ALLOW"
	PolicyDeny       PolicyDecision = "DENY"
	PolicyNoDecision PolicyDecision = "NO_DECISION"
)

// AccessPolicy represents a parsed YAML access policy ready for evaluation.
type AccessPolicy struct {
	ID       string         `json:"id"`
	Key      string         `json:"key"`
	Priority int            `json:"priority"`
	Enabled  bool           `json:"enabled"`
	Decision PolicyDecision `json:"decision"` // ALLOW or DENY
	Match    MatchBlock     `json:"match"`
	Unless   []Constraint   `json:"unless,omitempty"`
	Action   *PolicyAction  `json:"action,omitempty"`
}

// MatchBlock declares which taxonomy dimensions a policy applies to.
// An empty MatchBlock matches everything (catch-all).
type MatchBlock struct {
	DataUse      *MatchDimension `json:"data_use,omitempty"`
	DataCategory *MatchDimension `json:"data_category,omitempty"`
	DataSubject  *MatchDimension `json:"data_subject,omitempty"`
}

// MatchDimension specifies the any/all operators for one taxonomy dimension.
type MatchDimension struct {
	Any []string `json:"any,omitempty"` // at least one must match
	All []string `json:"all,omitempty"` // all must match
}

// ConstraintType identifies the kind of unless condition.
type ConstraintType string

const (
	ConstraintConsent     ConstraintType = "consent"
	ConstraintGeoLocation ConstraintType = "geo_location"
	ConstraintDataFlow    ConstraintType = "data_flow"
)

// Constraint is one condition in an unless block.
// All constraints in a block are AND'd — all must trigger for the unless to fire.
type Constraint struct {
	Type ConstraintType `json:"type"`

	// Consent fields
	PrivacyNoticeKey string `json:"privacy_notice_key,omitempty"`
	Requirement      string `json:"requirement,omitempty"` // opt_in, opt_out, not_opt_in, not_opt_out

	// Geo location fields
	Field    string   `json:"field,omitempty"`    // e.g. "environment.geo_location"
	Operator string   `json:"operator,omitempty"` // "in", "not_in", "any_of", "none_of"
	Values   []string `json:"values,omitempty"`

	// Data flow fields
	Direction string   `json:"direction,omitempty"` // "ingress", "egress"
	Systems   []string `json:"systems,omitempty"`
}

// PolicyAction is the action block from a decisive policy.
type PolicyAction struct {
	Message string `json:"message,omitempty"`
}

// AccessEvaluationRequest is the context provided to the policy evaluator
// after a PBAC purpose violation is detected.
type AccessEvaluationRequest struct {
	// From PBAC violation
	ConsumerID       string   `json:"consumer_id"`
	ConsumerName     string   `json:"consumer_name"`
	ConsumerPurposes []string `json:"consumer_purposes"`
	DatasetKey       string   `json:"dataset_key"`
	DatasetPurposes  []string `json:"dataset_purposes"`
	Collection       *string  `json:"collection,omitempty"`

	// For policy match resolution — from the consumer's system declarations
	SystemFidesKey string   `json:"system_fides_key,omitempty"`
	DataUses       []string `json:"data_uses,omitempty"`
	DataCategories []string `json:"data_categories,omitempty"`
	DataSubjects   []string `json:"data_subjects,omitempty"`

	// Runtime context for unless conditions
	Context map[string]interface{} `json:"context,omitempty"`
}

// EvaluatedPolicyInfo is the audit trail for a single policy evaluation.
type EvaluatedPolicyInfo struct {
	PolicyKey      string `json:"policy_key"`
	Priority       int    `json:"priority"`
	Matched        bool   `json:"matched"`
	Result         string `json:"result"` // "ALLOW", "DENY", "SUPPRESSED"
	UnlessTriggered bool  `json:"unless_triggered"`
}

// PolicyEvaluationResult is the output of evaluating access policies.
type PolicyEvaluationResult struct {
	Decision             PolicyDecision        `json:"decision"`
	DecisivePolicyKey    *string               `json:"decisive_policy_key,omitempty"`
	DecisivePolicyPriority *int                `json:"decisive_policy_priority,omitempty"`
	UnlessTriggered      bool                  `json:"unless_triggered"`
	EvaluatedPolicies    []EvaluatedPolicyInfo `json:"evaluated_policies"`
	Action               *PolicyAction         `json:"action,omitempty"`
	Reason               *string               `json:"reason,omitempty"`
}

// EvaluatePoliciesRequest is the JSON request body for the policy evaluation endpoint.
type EvaluatePoliciesRequest struct {
	Policies []AccessPolicy          `json:"policies"`
	Request  AccessEvaluationRequest `json:"request"`
}
