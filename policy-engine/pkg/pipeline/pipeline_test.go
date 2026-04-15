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
