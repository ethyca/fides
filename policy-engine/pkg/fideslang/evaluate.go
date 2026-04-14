package fideslang

import (
	"fmt"
	"time"
)

// EvaluatePolicyRule evaluates a single policy rule against a privacy declaration.
// Returns violations if the declaration violates the rule, empty slice otherwise.
func EvaluatePolicyRule(idx *TaxonomyIndex, rule *PolicyRule, decl *PrivacyDeclaration) []Violation {
	// Build hierarchies for data categories
	categoryHierarchies := make([][]string, 0, len(decl.DataCategories))
	for _, cat := range decl.DataCategories {
		hierarchy := idx.GetCategoryHierarchy(cat)
		categoryHierarchies = append(categoryHierarchies, hierarchy)
	}

	// Evaluate data categories
	categoryViolations := compareRuleToDeclaration(
		rule.DataCategories.Values,
		categoryHierarchies,
		rule.DataCategories.Matches,
	)

	// Build hierarchy for data use (single value, wrapped in slice of slices)
	useHierarchies := [][]string{idx.GetUseHierarchy(decl.DataUse)}

	// Evaluate data uses
	useViolations := compareRuleToDeclaration(
		rule.DataUses.Values,
		useHierarchies,
		rule.DataUses.Matches,
	)

	// Build hierarchies for data subjects
	subjectHierarchies := make([][]string, 0, len(decl.DataSubjects))
	for _, subj := range decl.DataSubjects {
		subjectHierarchies = append(subjectHierarchies, idx.GetSubjectHierarchy(subj))
	}

	// Evaluate data subjects
	subjectViolations := compareRuleToDeclaration(
		rule.DataSubjects.Values,
		subjectHierarchies,
		rule.DataSubjects.Matches,
	)

	// Violation occurs only if ALL THREE dimensions match (AND logic)
	if len(categoryViolations) > 0 && len(useViolations) > 0 && len(subjectViolations) > 0 {
		return []Violation{
			{
				Detail: fmt.Sprintf(
					"Declaration violates rule '%s'. Violated usage of data categories (%v) for data uses (%v) and subjects (%v)",
					rule.Name,
					categoryViolations,
					useViolations,
					subjectViolations,
				),
				ViolatingAttributes: ViolatingAttributes{
					DataCategories: categoryViolations,
					DataUses:       useViolations,
					DataSubjects:   subjectViolations,
				},
			},
		}
	}

	return nil
}

// compareRuleToDeclaration implements the match mode logic.
//
// Match modes:
//   - ANY: violation if ANY rule_type appears in ANY hierarchy
//   - ALL: violation if ALL declaration types are covered by rule types
//   - NONE: violation if NO matches occur (returns the non-matching types)
//   - OTHER: violation if declaration types are NOT in the rule (returns non-matching)
func compareRuleToDeclaration(ruleTypes []string, declarationHierarchies [][]string, matchMode MatchMode) []string {
	ruleTypeSet := make(map[string]bool, len(ruleTypes))
	for _, rt := range ruleTypes {
		ruleTypeSet[rt] = true
	}

	matched := make(map[string]bool)
	mismatched := make(map[string]bool)

	for _, hierarchy := range declarationHierarchies {
		if len(hierarchy) == 0 {
			continue
		}
		declaredType := hierarchy[0] // The leaf node (actual declared type)
		foundMatch := false

		for _, h := range hierarchy {
			if ruleTypeSet[h] {
				foundMatch = true
				break
			}
		}

		if foundMatch {
			matched[declaredType] = true
		} else {
			mismatched[declaredType] = true
		}
	}

	matchedList := mapKeysToSlice(matched)
	mismatchedList := mapKeysToSlice(mismatched)

	switch matchMode {
	case MatchAny:
		return matchedList

	case MatchAll:
		if len(matched) == len(declarationHierarchies) && len(declarationHierarchies) > 0 {
			return matchedList
		}
		return nil

	case MatchNone:
		if len(matched) == 0 && len(mismatched) > 0 {
			return mismatchedList
		}
		return nil

	case MatchOther:
		return mismatchedList

	default:
		return nil
	}
}

// Evaluate performs a full policy evaluation and returns the response.
func Evaluate(req *EvaluateRequest) *EvaluateResponse {
	start := time.Now()

	idx := NewTaxonomyIndex(&req.Taxonomy)
	violations := EvaluatePolicyRule(idx, &req.PolicyRule, &req.PrivacyDeclaration)

	status := "PASS"
	if len(violations) > 0 {
		status = "FAIL"
	}

	if violations == nil {
		violations = []Violation{}
	}

	return &EvaluateResponse{
		Status:           status,
		Violations:       violations,
		EvaluationTimeUs: time.Since(start).Microseconds(),
	}
}

func mapKeysToSlice(m map[string]bool) []string {
	if len(m) == 0 {
		return nil
	}
	result := make([]string, 0, len(m))
	for k := range m {
		result = append(result, k)
	}
	return result
}
