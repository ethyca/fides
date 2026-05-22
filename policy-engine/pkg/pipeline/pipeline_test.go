package pipeline

import (
	"path/filepath"
	"testing"

	"github.com/ethyca/fides/policy-engine/pkg/fixtures"
	"github.com/ethyca/fides/policy-engine/pkg/pbac"
)

// loadFixtures loads the demo fixtures from ../../pbac/. Fails the test
// outright if any directory is missing or malformed so callers don't
// have to check each step.
func loadFixtures(t *testing.T) Fixtures {
	t.Helper()
	root := filepath.Join("..", "..", "..", "pbac")

	consumers, err := fixtures.LoadConsumers(filepath.Join(root, "consumers"))
	if err != nil {
		t.Fatalf("load consumers: %v", err)
	}
	purposes, err := fixtures.LoadPurposes(filepath.Join(root, "purposes"))
	if err != nil {
		t.Fatalf("load purposes: %v", err)
	}
	datasets, err := fixtures.LoadDatasets(filepath.Join(root, "datasets"))
	if err != nil {
		t.Fatalf("load datasets: %v", err)
	}
	policies, err := fixtures.LoadPolicies(filepath.Join(root, "policies"))
	if err != nil {
		t.Fatalf("load policies: %v", err)
	}
	return Fixtures{
		Consumers: consumers,
		Purposes:  purposes,
		Datasets:  datasets,
		Policies:  policies,
	}
}

// aliceQuery is a convenience for building a single-table input attributed
// to alice@demo.example.
func aliceQuery(collection, queryID string) Input {
	return Input{
		QueryID:  queryID,
		Identity: "alice@demo.example",
		Tables:   []TableRef{{Collection: collection, QualifiedName: collection}},
	}
}

// ── Alice (analytics-team) — all four scenarios from pbac/entries/alice.txt

func TestAlice_PageViews_Compliant(t *testing.T) {
	f := loadFixtures(t)
	// analytics ∩ events.data_purposes = {analytics} -> compliant
	rec := Evaluate(f, aliceQuery("page_views", "q1"))

	if !rec.IsCompliant {
		t.Fatalf("expected compliant, got violations=%+v gaps=%+v", rec.Violations, rec.Gaps)
	}
	if len(rec.DatasetKeys) != 1 || rec.DatasetKeys[0] != "events" {
		t.Errorf("expected dataset events, got %v", rec.DatasetKeys)
	}
}

func TestAlice_Orders_ViolationSuppressedByPolicy(t *testing.T) {
	f := loadFixtures(t)
	// sales.orders at dataset level is billing; alice has analytics ->
	// purpose violation. The allow-analytics-on-billing-data policy
	// matches data_use essential.service.payment_processing -> suppress.
	rec := Evaluate(f, aliceQuery("orders", "q2"))

	if !rec.IsCompliant {
		t.Fatalf("expected compliant (violation suppressed), got compliant=%v", rec.IsCompliant)
	}
	if len(rec.Violations) != 1 {
		t.Fatalf("expected 1 violation (suppressed), got %d", len(rec.Violations))
	}
	v := rec.Violations[0]
	if v.SuppressedByPolicy == nil {
		t.Fatalf("expected violation to be suppressed by a policy")
	}
	if *v.SuppressedByPolicy != "allow-analytics-on-billing-data" {
		t.Errorf("expected policy key 'allow-analytics-on-billing-data', got %q", *v.SuppressedByPolicy)
	}
	// The ALLOW policy in the fixture set declares an action message; the
	// pipeline should surface it on the suppressed violation even though
	// EvaluatePolicies by design only returns Action on DENY decisions.
	if v.SuppressedByAction == nil {
		t.Fatalf("expected SuppressedByAction to be populated from the policy's action block")
	}
}

func TestAlice_Invoices_CompliantViaCollectionPurpose(t *testing.T) {
	f := loadFixtures(t)
	// sales.invoices collection adds analytics -> no violation needed,
	// no policy needed.
	rec := Evaluate(f, aliceQuery("invoices", "q3"))

	if !rec.IsCompliant {
		t.Fatalf("expected compliant, got violations=%+v gaps=%+v", rec.Violations, rec.Gaps)
	}
	if len(rec.Violations) != 0 {
		t.Errorf("expected 0 violations (collection-level analytics), got %d", len(rec.Violations))
	}
}

func TestAlice_Campaigns_ViolationStands(t *testing.T) {
	f := loadFixtures(t)
	// campaigns is marketing; no policy matches -> violation stands
	rec := Evaluate(f, aliceQuery("campaigns", "q4"))

	if rec.IsCompliant {
		t.Fatalf("expected non-compliant")
	}
	if len(rec.Violations) != 1 {
		t.Fatalf("expected 1 violation, got %d", len(rec.Violations))
	}
	if rec.Violations[0].SuppressedByPolicy != nil {
		t.Errorf("expected violation NOT suppressed, got %s", *rec.Violations[0].SuppressedByPolicy)
	}
}

// ── Other identities exercise the three gap types

func TestBob_UnknownTable_UnconfiguredDatasetGap(t *testing.T) {
	f := loadFixtures(t)
	rec := Evaluate(f, Input{
		QueryID:  "q5",
		Identity: "bob@demo.example",
		Tables: []TableRef{
			{Collection: "cold_storage", QualifiedName: "archive.legacy.cold_storage"},
		},
	})

	if len(rec.Gaps) == 0 {
		t.Fatalf("expected UNCONFIGURED_DATASET gap")
	}
	if rec.Gaps[0].GapType != pbac.GapUnconfiguredDataset {
		t.Errorf("expected gap type unconfigured_dataset, got %s", rec.Gaps[0].GapType)
	}
	if rec.Gaps[0].Identifier != "archive.legacy.cold_storage" {
		t.Errorf("expected qualified-name identifier, got %q", rec.Gaps[0].Identifier)
	}
}

func TestCarol_UnknownIdentity_UnresolvedIdentityGap(t *testing.T) {
	f := loadFixtures(t)
	rec := Evaluate(f, Input{
		QueryID:  "q6",
		Identity: "carol@demo.example",
		Tables:   []TableRef{{Collection: "page_views", QualifiedName: "page_views"}},
	})

	if len(rec.Gaps) != 1 {
		t.Fatalf("expected 1 gap, got %d", len(rec.Gaps))
	}
	if rec.Gaps[0].GapType != pbac.GapUnresolvedIdentity {
		t.Errorf("expected unresolved_identity, got %s", rec.Gaps[0].GapType)
	}
}

func TestDave_ConsumerWithNoPurposes_UnconfiguredConsumerGap(t *testing.T) {
	f := loadFixtures(t)
	// dave is in onboarding-unconfigured consumer which has no purposes —
	// identity resolves but purposes are empty -> reclassified as
	// UNCONFIGURED_CONSUMER.
	rec := Evaluate(f, Input{
		QueryID:  "q7",
		Identity: "dave@demo.example",
		Tables:   []TableRef{{Collection: "page_views", QualifiedName: "page_views"}},
	})

	if len(rec.Gaps) != 1 {
		t.Fatalf("expected 1 gap, got %d", len(rec.Gaps))
	}
	if rec.Gaps[0].GapType != pbac.GapUnconfiguredConsumer {
		t.Errorf("expected unconfigured_consumer, got %s", rec.Gaps[0].GapType)
	}
}

// ── Data category resolution from columns

func TestResolveDataCategories_SpecificColumns(t *testing.T) {
	fieldCategories := map[string]map[string][]string{
		"users": {
			"email": {"user.contact.email"},
			"phone": {"user.contact.phone_number"},
			"ssn":   {"user.government_id"},
		},
	}
	columnsByDataset := map[string]map[string][]string{
		"mydb": {"users": {"email", "phone"}},
	}

	cats := resolveDataCategories("mydb", "users", columnsByDataset, fieldCategories)
	if len(cats) != 2 {
		t.Fatalf("expected 2 categories, got %d: %v", len(cats), cats)
	}
	expected := map[string]bool{"user.contact.email": true, "user.contact.phone_number": true}
	for _, c := range cats {
		if !expected[c] {
			t.Errorf("unexpected category %q", c)
		}
	}
}

func TestResolveDataCategories_SelectStar_AllCategories(t *testing.T) {
	fieldCategories := map[string]map[string][]string{
		"users": {
			"email": {"user.contact.email"},
			"ssn":   {"user.government_id"},
		},
	}
	// Empty columns = SELECT *
	columnsByDataset := map[string]map[string][]string{}

	cats := resolveDataCategories("mydb", "users", columnsByDataset, fieldCategories)
	if len(cats) != 2 {
		t.Fatalf("expected 2 categories (all fields), got %d: %v", len(cats), cats)
	}
}

func TestResolveDataCategories_NoFieldCategories(t *testing.T) {
	cats := resolveDataCategories("mydb", "users", nil, nil)
	if cats != nil {
		t.Errorf("expected nil, got %v", cats)
	}
}

func TestResolveDataCategories_UnknownColumns(t *testing.T) {
	fieldCategories := map[string]map[string][]string{
		"users": {
			"email": {"user.contact.email"},
		},
	}
	columnsByDataset := map[string]map[string][]string{
		"mydb": {"users": {"unknown_col"}},
	}

	cats := resolveDataCategories("mydb", "users", columnsByDataset, fieldCategories)
	if cats != nil {
		t.Errorf("expected nil for unknown columns, got %v", cats)
	}
}

func TestEvaluate_DataCategoryPolicyMatchesResolvedColumns(t *testing.T) {
	f := loadFixtures(t)

	// Add field categories to the fixture's datasets
	f.Datasets.FieldCategories = map[string]map[string][]string{
		"orders": {
			"total":      {"user.financial"},
			"email":      {"user.contact.email"},
			"product_id": {"system.operations"},
		},
	}

	// Add an ALLOW policy that matches on data_category user.financial.
	// This should suppress the violation when columns include "total"
	// (which has category user.financial).
	enabled := true
	f.Policies = append(f.Policies, pbac.AccessPolicy{
		Key:      "allow-financial-columns",
		Priority: 999,
		Enabled:  &enabled,
		Decision: pbac.PolicyAllow,
		Match: pbac.MatchBlock{
			DataCategory: &pbac.MatchDimension{
				Any: []string{"user.financial"},
			},
		},
	})

	// Alice querying orders with "total" column (user.financial category)
	rec := Evaluate(f, Input{
		QueryID:  "q-cats-match",
		Identity: "alice@demo.example",
		Tables: []TableRef{
			{
				Collection:    "orders",
				QualifiedName: "sales.orders",
				Columns:       []string{"total"},
			},
		},
	})

	if len(rec.Violations) == 0 {
		t.Fatalf("expected at least 1 violation")
	}
	v := rec.Violations[0]
	if v.SuppressedByPolicy == nil || *v.SuppressedByPolicy != "allow-financial-columns" {
		t.Fatalf("expected violation suppressed by allow-financial-columns, got %v", v.SuppressedByPolicy)
	}
}

func TestEvaluate_DataCategoryPolicyDoesNotMatchWhenColumnsLackCategory(t *testing.T) {
	f := loadFixtures(t)

	f.Datasets.FieldCategories = map[string]map[string][]string{
		"orders": {
			"total":      {"user.financial"},
			"product_id": {"system.operations"},
		},
	}

	// ALLOW policy that matches user.financial
	enabled := true
	f.Policies = append(f.Policies, pbac.AccessPolicy{
		Key:      "allow-financial-columns",
		Priority: 999,
		Enabled:  &enabled,
		Decision: pbac.PolicyAllow,
		Match: pbac.MatchBlock{
			DataCategory: &pbac.MatchDimension{
				Any: []string{"user.financial"},
			},
		},
	})

	// Query only accesses product_id (system.operations), NOT total (user.financial)
	rec := Evaluate(f, Input{
		QueryID:  "q-cats-no-match",
		Identity: "alice@demo.example",
		Tables: []TableRef{
			{
				Collection:    "orders",
				QualifiedName: "sales.orders",
				Columns:       []string{"product_id"},
			},
		},
	})

	if len(rec.Violations) == 0 {
		t.Fatalf("expected at least 1 violation")
	}
	v := rec.Violations[0]
	if v.SuppressedByPolicy != nil && *v.SuppressedByPolicy == "allow-financial-columns" {
		t.Fatalf("policy should NOT match — query didn't access user.financial columns")
	}
}

func TestEvaluate_SelectStarResolvesAllFieldCategories(t *testing.T) {
	f := loadFixtures(t)

	f.Datasets.FieldCategories = map[string]map[string][]string{
		"orders": {
			"total":      {"user.financial"},
			"product_id": {"system.operations"},
		},
	}

	// ALLOW policy matching user.financial
	enabled := true
	f.Policies = append(f.Policies, pbac.AccessPolicy{
		Key:      "allow-financial-columns",
		Priority: 999,
		Enabled:  &enabled,
		Decision: pbac.PolicyAllow,
		Match: pbac.MatchBlock{
			DataCategory: &pbac.MatchDimension{
				Any: []string{"user.financial"},
			},
		},
	})

	// SELECT * — no columns specified, should resolve all categories
	rec := Evaluate(f, Input{
		QueryID:  "q-cats-star",
		Identity: "alice@demo.example",
		Tables: []TableRef{
			{
				Collection:    "orders",
				QualifiedName: "sales.orders",
				// No Columns = SELECT *
			},
		},
	})

	if len(rec.Violations) == 0 {
		t.Fatalf("expected at least 1 violation")
	}
	v := rec.Violations[0]
	// SELECT * includes user.financial, so the policy should match
	if v.SuppressedByPolicy == nil || *v.SuppressedByPolicy != "allow-financial-columns" {
		t.Fatalf("expected SELECT * to resolve all categories including user.financial, got suppressed_by=%v", v.SuppressedByPolicy)
	}
}

// ── Table resolution: case-insensitive, multi-part qualified names

func TestTableResolution_CaseInsensitive(t *testing.T) {
	f := loadFixtures(t)
	rec := Evaluate(f, Input{
		Identity: "alice@demo.example",
		Tables:   []TableRef{{Collection: "PAGE_VIEWS", QualifiedName: "PAGE_VIEWS"}},
	})
	if len(rec.DatasetKeys) != 1 || rec.DatasetKeys[0] != "events" {
		t.Errorf("expected case-insensitive table resolution, got %v", rec.DatasetKeys)
	}
}
