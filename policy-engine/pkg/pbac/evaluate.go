package pbac

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

	var violations []PurposeViolation
	var gaps []EvaluationGap
	totalAccesses := 0

	consumerPurposeSet := toSet(consumer.PurposeKeys)

	// Rule 1: consumer has no purposes — record as identity gap
	if len(consumer.PurposeKeys) == 0 {
		for datasetKey := range datasets {
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

	for datasetKey, dsPurposes := range datasets {
		dk := datasetKey
		datasetCollections := collections[datasetKey]

		if len(datasetCollections) > 0 {
			for _, collection := range datasetCollections {
				totalAccesses++
				col := collection
				result := checkAccess(consumerPurposeSet, consumer, &dsPurposes, dk, &col)
				switch r := result.(type) {
				case PurposeViolation:
					violations = append(violations, r)
				case EvaluationGap:
					gaps = append(gaps, r)
				}
			}
		} else {
			totalAccesses++
			result := checkAccess(consumerPurposeSet, consumer, &dsPurposes, dk, nil)
			switch r := result.(type) {
			case PurposeViolation:
				violations = append(violations, r)
			case EvaluationGap:
				gaps = append(gaps, r)
			}
		}
	}

	return PurposeEvaluationResult{
		Violations:    ensureViolations(violations),
		Gaps:          ensureGaps(gaps),
		TotalAccesses: totalAccesses,
	}
}

// checkAccess checks a single dataset/collection access against consumer purposes.
// Returns a PurposeViolation, EvaluationGap, or nil (compliant).
func checkAccess(
	consumerPurposeSet map[string]bool,
	consumer ConsumerPurposes,
	dsPurposes *DatasetPurposes,
	datasetKey string,
	collection *string,
) interface{} {
	col := ""
	if collection != nil {
		col = *collection
	}
	effective := dsPurposes.EffectivePurposes(col)

	// Rule 3: no effective purposes → dataset gap
	if len(effective) == 0 {
		dk := datasetKey
		return EvaluationGap{
			GapType:    GapUnconfiguredDataset,
			Identifier: datasetKey,
			DatasetKey: &dk,
			Reason:     "Dataset has no declared purposes",
		}
	}

	// Rule 2: no overlap → violation
	if !intersects(consumerPurposeSet, effective) {
		return PurposeViolation{
			ConsumerID:       consumer.ConsumerID,
			ConsumerName:     consumer.ConsumerName,
			DatasetKey:       datasetKey,
			Collection:       collection,
			ConsumerPurposes: sortedKeys(consumerPurposeSet),
			DatasetPurposes:  sortedKeys(effective),
			Reason:           violationReason(consumerPurposeSet, effective),
		}
	}

	// Compliant
	return nil
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
