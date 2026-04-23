package pbac

import "sort"

// EvaluatePurpose checks dataset accesses against purpose assignments.
//
// Rules (matching the Python engine in fides/service/pbac/evaluate.py):
//
//  1. If the consumer has NO declared purposes, every dataset access is
//     recorded as an identity gap (not a violation).
//  2. If a dataset has declared purposes AND the consumer's purposes do not
//     intersect with the dataset's effective purposes, it is a violation.
//  3. If a dataset has NO declared purposes, it is recorded as a dataset
//     gap (not a violation).
func EvaluatePurpose(
	consumer ConsumerPurposes,
	datasets map[string]DatasetPurposes,
	collections map[string][]string,
) PurposeEvaluationResult {
	if collections == nil {
		collections = map[string][]string{}
	}

	// Sort dataset keys for deterministic iteration order.
	// Go map iteration is randomized; sorting ensures stable output
	// for audit trails, diff-ability, and test reliability.
	datasetKeys := make([]string, 0, len(datasets))
	for k := range datasets {
		datasetKeys = append(datasetKeys, k)
	}
	sort.Strings(datasetKeys)

	var violations []PurposeViolation
	var gaps []EvaluationGap
	totalAccesses := 0

	consumerPurposeSet := toSet(consumer.PurposeKeys)

	// Rule 1: consumer has no purposes — record as identity gap
	if len(consumer.PurposeKeys) == 0 {
		for _, datasetKey := range datasetKeys {
			totalAccesses++
			dk := datasetKey
			gaps = append(gaps, EvaluationGap{
				GapType:    GapUnresolvedIdentity,
				Identifier: consumer.ConsumerID,
				DatasetKey: &dk,
				Reason:     "Consumer has no declared purposes",
			})
		}
		return PurposeEvaluationResult{
			Violations:    ensureViolations(violations),
			Gaps:          ensureGaps(gaps),
			TotalAccesses: totalAccesses,
		}
	}

	for _, datasetKey := range datasetKeys {
		dsPurposes := datasets[datasetKey]
		dk := datasetKey
		datasetCollections := collections[datasetKey]

		if len(datasetCollections) > 0 {
			for _, collection := range datasetCollections {
				totalAccesses++
				col := collection
				result := checkAccess(consumerPurposeSet, consumer, &dsPurposes, dk, &col)
				if result.Violation != nil {
					violations = append(violations, *result.Violation)
				} else if result.Gap != nil {
					gaps = append(gaps, *result.Gap)
				}
			}
		} else {
			totalAccesses++
			result := checkAccess(consumerPurposeSet, consumer, &dsPurposes, dk, nil)
			if result.Violation != nil {
				violations = append(violations, *result.Violation)
			} else if result.Gap != nil {
				gaps = append(gaps, *result.Gap)
			}
		}
	}

	return PurposeEvaluationResult{
		Violations:    ensureViolations(violations),
		Gaps:          ensureGaps(gaps),
		TotalAccesses: totalAccesses,
	}
}

// accessCheckResult holds the outcome of a single dataset/collection check.
// Exactly one of Violation or Gap is set, or both are nil (compliant).
type accessCheckResult struct {
	Violation *PurposeViolation
	Gap       *EvaluationGap
}

// checkAccess checks a single dataset/collection access against consumer purposes.
func checkAccess(
	consumerPurposeSet map[string]bool,
	consumer ConsumerPurposes,
	dsPurposes *DatasetPurposes,
	datasetKey string,
	collection *string,
) accessCheckResult {
	col := ""
	if collection != nil {
		col = *collection
	}
	effective := dsPurposes.EffectivePurposes(col)

	// Rule 3: no effective purposes → dataset gap
	if len(effective) == 0 {
		dk := datasetKey
		return accessCheckResult{Gap: &EvaluationGap{
			GapType:    GapUnconfiguredDataset,
			Identifier: datasetKey,
			DatasetKey: &dk,
			Reason:     "Dataset has no declared purposes",
		}}
	}

	// Rule 2: no overlap → violation
	if !intersects(consumerPurposeSet, effective) {
		return accessCheckResult{Violation: &PurposeViolation{
			ConsumerID:       consumer.ConsumerID,
			ConsumerName:     consumer.ConsumerName,
			DatasetKey:       datasetKey,
			Collection:       collection,
			ConsumerPurposes: sortedKeys(consumerPurposeSet),
			DatasetPurposes:  sortedKeys(effective),
			Reason:           violationReason(consumerPurposeSet, effective),
		}}
	}

	// Compliant
	return accessCheckResult{}
}

// Ensure non-nil slices for JSON serialization.
func ensureViolations(v []PurposeViolation) []PurposeViolation {
	if v == nil {
		return []PurposeViolation{}
	}
	return v
}

func ensureGaps(g []EvaluationGap) []EvaluationGap {
	if g == nil {
		return []EvaluationGap{}
	}
	return g
}
