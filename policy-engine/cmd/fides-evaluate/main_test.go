package main

import (
	"bytes"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
)

var binaryPath string

func TestMain(m *testing.M) {
	// Build the binary once before all tests
	dir, err := os.MkdirTemp("", "fides-evaluate-test")
	if err != nil {
		panic(err)
	}
	defer os.RemoveAll(dir)

	binaryPath = filepath.Join(dir, "fides-evaluate")
	cmd := exec.Command("go", "build", "-o", binaryPath, ".")
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		panic("failed to build binary: " + err.Error())
	}

	os.Exit(m.Run())
}

func runCLI(t *testing.T, command string, input string) (string, string, int) {
	t.Helper()
	cmd := exec.Command(binaryPath, command)
	cmd.Stdin = bytes.NewBufferString(input)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err := cmd.Run()
	exitCode := 0
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			exitCode = exitErr.ExitCode()
		} else {
			t.Fatalf("unexpected error running CLI: %v", err)
		}
	}
	return stdout.String(), stderr.String(), exitCode
}

func runCLIWithFile(t *testing.T, command string, content string) (string, string, int) {
	t.Helper()
	f, err := os.CreateTemp("", "fides-evaluate-*.json")
	if err != nil {
		t.Fatal(err)
	}
	defer os.Remove(f.Name())
	if _, err := f.WriteString(content); err != nil {
		t.Fatal(err)
	}
	f.Close()

	cmd := exec.Command(binaryPath, command, f.Name())
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err = cmd.Run()
	exitCode := 0
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			exitCode = exitErr.ExitCode()
		} else {
			t.Fatalf("unexpected error running CLI: %v", err)
		}
	}
	return stdout.String(), stderr.String(), exitCode
}

// ── purpose command tests ────────────────────────────────────────────

func TestCLI_Purpose_Compliant(t *testing.T) {
	input := `{
		"consumer": {"consumer_id": "c1", "consumer_name": "Billing", "purpose_keys": ["billing"]},
		"datasets": {"billing_db": {"dataset_key": "billing_db", "purpose_keys": ["billing"]}}
	}`

	stdout, _, exitCode := runCLI(t, "purpose", input)
	if exitCode != 0 {
		t.Fatalf("expected exit 0, got %d", exitCode)
	}

	var result map[string]interface{}
	if err := json.Unmarshal([]byte(stdout), &result); err != nil {
		t.Fatalf("invalid JSON output: %v\nstdout: %s", err, stdout)
	}

	violations := result["violations"].([]interface{})
	if len(violations) != 0 {
		t.Errorf("expected 0 violations, got %d", len(violations))
	}
	if result["total_accesses"].(float64) != 1 {
		t.Errorf("expected 1 total access")
	}
}

func TestCLI_Purpose_Violation(t *testing.T) {
	input := `{
		"consumer": {"consumer_id": "c1", "consumer_name": "Analytics", "purpose_keys": ["analytics"]},
		"datasets": {"billing_db": {"dataset_key": "billing_db", "purpose_keys": ["billing"]}}
	}`

	stdout, _, exitCode := runCLI(t, "purpose", input)
	if exitCode != 0 {
		t.Fatalf("expected exit 0, got %d", exitCode)
	}

	var result map[string]interface{}
	json.Unmarshal([]byte(stdout), &result)

	violations := result["violations"].([]interface{})
	if len(violations) != 1 {
		t.Errorf("expected 1 violation, got %d", len(violations))
	}
}

func TestCLI_Purpose_Gap(t *testing.T) {
	input := `{
		"consumer": {"consumer_id": "c1", "consumer_name": "Unknown", "purpose_keys": []},
		"datasets": {"db1": {"dataset_key": "db1", "purpose_keys": ["billing"]}}
	}`

	stdout, _, exitCode := runCLI(t, "purpose", input)
	if exitCode != 0 {
		t.Fatalf("expected exit 0, got %d", exitCode)
	}

	var result map[string]interface{}
	json.Unmarshal([]byte(stdout), &result)

	gaps := result["gaps"].([]interface{})
	if len(gaps) != 1 {
		t.Errorf("expected 1 gap, got %d", len(gaps))
	}
	gap := gaps[0].(map[string]interface{})
	if gap["gap_type"] != "unresolved_identity" {
		t.Errorf("expected unresolved_identity, got %s", gap["gap_type"])
	}
}

func TestCLI_Purpose_WithCollections(t *testing.T) {
	input := `{
		"consumer": {"consumer_id": "c1", "consumer_name": "Accountant", "purpose_keys": ["accounting"]},
		"datasets": {
			"billing_db": {
				"dataset_key": "billing_db",
				"purpose_keys": ["billing"],
				"collection_purposes": {"invoices": ["accounting"]}
			}
		},
		"collections": {"billing_db": ["invoices"]}
	}`

	stdout, _, exitCode := runCLI(t, "purpose", input)
	if exitCode != 0 {
		t.Fatalf("expected exit 0, got %d", exitCode)
	}

	var result map[string]interface{}
	json.Unmarshal([]byte(stdout), &result)

	// accounting overlaps with billing_db.invoices effective purposes {billing, accounting}
	violations := result["violations"].([]interface{})
	if len(violations) != 0 {
		t.Errorf("expected 0 violations (collection purpose overlap), got %d", len(violations))
	}
}

func TestCLI_Purpose_FromFile(t *testing.T) {
	input := `{
		"consumer": {"consumer_id": "c1", "consumer_name": "Test", "purpose_keys": ["analytics"]},
		"datasets": {"db1": {"dataset_key": "db1", "purpose_keys": ["analytics"]}}
	}`

	stdout, _, exitCode := runCLIWithFile(t, "purpose", input)
	if exitCode != 0 {
		t.Fatalf("expected exit 0, got %d", exitCode)
	}

	var result map[string]interface{}
	if err := json.Unmarshal([]byte(stdout), &result); err != nil {
		t.Fatalf("invalid JSON: %v", err)
	}

	violations := result["violations"].([]interface{})
	if len(violations) != 0 {
		t.Errorf("expected 0 violations, got %d", len(violations))
	}
}

func TestCLI_Purpose_MultipleDatasets(t *testing.T) {
	input := `{
		"consumer": {"consumer_id": "c1", "consumer_name": "Analyst", "purpose_keys": ["analytics"]},
		"datasets": {
			"analytics_db": {"dataset_key": "analytics_db", "purpose_keys": ["analytics"]},
			"billing_db": {"dataset_key": "billing_db", "purpose_keys": ["billing"]},
			"empty_db": {"dataset_key": "empty_db", "purpose_keys": []}
		}
	}`

	stdout, _, exitCode := runCLI(t, "purpose", input)
	if exitCode != 0 {
		t.Fatalf("expected exit 0, got %d", exitCode)
	}

	var result map[string]interface{}
	json.Unmarshal([]byte(stdout), &result)

	if result["total_accesses"].(float64) != 3 {
		t.Errorf("expected 3 total accesses, got %v", result["total_accesses"])
	}

	violations := result["violations"].([]interface{})
	gaps := result["gaps"].([]interface{})
	if len(violations) != 1 {
		t.Errorf("expected 1 violation (billing_db), got %d", len(violations))
	}
	if len(gaps) != 1 {
		t.Errorf("expected 1 gap (empty_db), got %d", len(gaps))
	}
}

// ── policies command tests ───────────────────────────────────────────

func TestCLI_Policies_Allow(t *testing.T) {
	input := `{
		"policies": [
			{
				"id": "p1", "key": "allow-marketing", "priority": 100, "enabled": true,
				"decision": "ALLOW",
				"match": {"data_use": {"any": ["marketing"]}}
			}
		],
		"request": {
			"consumer_id": "c1", "consumer_name": "Marketing",
			"data_uses": ["marketing.advertising"]
		}
	}`

	stdout, _, exitCode := runCLI(t, "policies", input)
	if exitCode != 0 {
		t.Fatalf("expected exit 0, got %d", exitCode)
	}

	var result map[string]interface{}
	json.Unmarshal([]byte(stdout), &result)

	if result["decision"] != "ALLOW" {
		t.Errorf("expected ALLOW, got %s", result["decision"])
	}
	if result["decisive_policy_key"] != "allow-marketing" {
		t.Errorf("expected decisive key 'allow-marketing', got %v", result["decisive_policy_key"])
	}
}

func TestCLI_Policies_Deny(t *testing.T) {
	input := `{
		"policies": [
			{
				"id": "p1", "key": "deny-all", "priority": 0, "enabled": true,
				"decision": "DENY",
				"match": {},
				"action": {"message": "Access denied by default"}
			}
		],
		"request": {
			"consumer_id": "c1", "consumer_name": "Anyone",
			"data_uses": ["essential"]
		}
	}`

	stdout, _, exitCode := runCLI(t, "policies", input)
	if exitCode != 0 {
		t.Fatalf("expected exit 0, got %d", exitCode)
	}

	var result map[string]interface{}
	json.Unmarshal([]byte(stdout), &result)

	if result["decision"] != "DENY" {
		t.Errorf("expected DENY, got %s", result["decision"])
	}
	action := result["action"].(map[string]interface{})
	if action["message"] != "Access denied by default" {
		t.Errorf("expected action message")
	}
}

func TestCLI_Policies_NoDecision(t *testing.T) {
	input := `{
		"policies": [
			{
				"id": "p1", "key": "deny-financial", "priority": 100, "enabled": true,
				"decision": "DENY",
				"match": {"data_category": {"any": ["user.financial"]}}
			}
		],
		"request": {
			"consumer_id": "c1", "consumer_name": "Test",
			"data_categories": ["system.operations"]
		}
	}`

	stdout, _, exitCode := runCLI(t, "policies", input)
	if exitCode != 0 {
		t.Fatalf("expected exit 0, got %d", exitCode)
	}

	var result map[string]interface{}
	json.Unmarshal([]byte(stdout), &result)

	if result["decision"] != "NO_DECISION" {
		t.Errorf("expected NO_DECISION, got %s", result["decision"])
	}
}

func TestCLI_Policies_UnlessInverts(t *testing.T) {
	input := `{
		"policies": [
			{
				"id": "p1", "key": "allow-unless-optout", "priority": 100, "enabled": true,
				"decision": "ALLOW",
				"match": {"data_use": {"any": ["marketing"]}},
				"unless": [
					{"type": "consent", "privacy_notice_key": "do_not_sell", "requirement": "opt_out"}
				],
				"action": {"message": "User opted out"}
			}
		],
		"request": {
			"consumer_id": "c1", "consumer_name": "Marketing",
			"data_uses": ["marketing.advertising"],
			"context": {
				"consent": {"do_not_sell": "opt_out"}
			}
		}
	}`

	stdout, _, exitCode := runCLI(t, "policies", input)
	if exitCode != 0 {
		t.Fatalf("expected exit 0, got %d", exitCode)
	}

	var result map[string]interface{}
	json.Unmarshal([]byte(stdout), &result)

	if result["decision"] != "DENY" {
		t.Errorf("expected DENY (inverted ALLOW), got %s", result["decision"])
	}
	if result["unless_triggered"] != true {
		t.Error("expected unless_triggered=true")
	}
}

func TestCLI_Policies_PriorityOrdering(t *testing.T) {
	input := `{
		"policies": [
			{
				"id": "p1", "key": "low-allow", "priority": 10, "enabled": true,
				"decision": "ALLOW",
				"match": {}
			},
			{
				"id": "p2", "key": "high-deny", "priority": 200, "enabled": true,
				"decision": "DENY",
				"match": {},
				"action": {"message": "Highest priority wins"}
			}
		],
		"request": {
			"consumer_id": "c1", "consumer_name": "Test",
			"data_uses": ["marketing"]
		}
	}`

	stdout, _, exitCode := runCLI(t, "policies", input)
	if exitCode != 0 {
		t.Fatalf("expected exit 0, got %d", exitCode)
	}

	var result map[string]interface{}
	json.Unmarshal([]byte(stdout), &result)

	if result["decision"] != "DENY" {
		t.Errorf("expected DENY (high priority), got %s", result["decision"])
	}
	if result["decisive_policy_key"] != "high-deny" {
		t.Errorf("expected decisive key 'high-deny', got %v", result["decisive_policy_key"])
	}
}

func TestCLI_Policies_FromFile(t *testing.T) {
	input := `{
		"policies": [],
		"request": {"consumer_id": "c1", "consumer_name": "Test"}
	}`

	stdout, _, exitCode := runCLIWithFile(t, "policies", input)
	if exitCode != 0 {
		t.Fatalf("expected exit 0, got %d", exitCode)
	}

	var result map[string]interface{}
	json.Unmarshal([]byte(stdout), &result)

	if result["decision"] != "NO_DECISION" {
		t.Errorf("expected NO_DECISION, got %s", result["decision"])
	}
}

// ── Error handling tests ─────────────────────────────────────────────

func TestCLI_NoArgs_ExitsNonZero(t *testing.T) {
	cmd := exec.Command(binaryPath)
	err := cmd.Run()
	if err == nil {
		t.Error("expected non-zero exit with no args")
	}
}

func TestCLI_UnknownCommand_ExitsNonZero(t *testing.T) {
	_, stderr, exitCode := runCLI(t, "bogus", "{}")
	if exitCode == 0 {
		t.Error("expected non-zero exit for unknown command")
	}
	if !bytes.Contains([]byte(stderr), []byte("Unknown command")) {
		t.Errorf("expected 'Unknown command' in stderr, got: %s", stderr)
	}
}

func TestCLI_InvalidJSON_ExitsNonZero(t *testing.T) {
	_, stderr, exitCode := runCLI(t, "purpose", "not valid json")
	if exitCode == 0 {
		t.Error("expected non-zero exit for invalid JSON")
	}
	if !bytes.Contains([]byte(stderr), []byte("Error parsing JSON")) {
		t.Errorf("expected parse error in stderr, got: %s", stderr)
	}
}

func TestCLI_MissingFile_ExitsNonZero(t *testing.T) {
	cmd := exec.Command(binaryPath, "purpose", "/tmp/nonexistent-file-fides-test.json")
	err := cmd.Run()
	if err == nil {
		t.Error("expected non-zero exit for missing file")
	}
}

func TestCLI_EmptyInput_Purpose(t *testing.T) {
	// Empty JSON object — consumer and datasets will have zero values
	stdout, _, exitCode := runCLI(t, "purpose", "{}")
	if exitCode != 0 {
		t.Fatalf("expected exit 0, got %d", exitCode)
	}

	var result map[string]interface{}
	json.Unmarshal([]byte(stdout), &result)

	// Empty datasets → 0 accesses, no violations, no gaps
	if result["total_accesses"].(float64) != 0 {
		t.Errorf("expected 0 accesses, got %v", result["total_accesses"])
	}
}

func TestCLI_OutputIsValidJSON(t *testing.T) {
	input := `{
		"consumer": {"consumer_id": "c1", "consumer_name": "Test", "purpose_keys": ["x"]},
		"datasets": {"d1": {"dataset_key": "d1", "purpose_keys": ["y"]}}
	}`

	stdout, _, exitCode := runCLI(t, "purpose", input)
	if exitCode != 0 {
		t.Fatalf("expected exit 0, got %d", exitCode)
	}

	// Verify it's valid JSON that can be round-tripped
	var parsed interface{}
	if err := json.Unmarshal([]byte(stdout), &parsed); err != nil {
		t.Errorf("output is not valid JSON: %v\noutput: %s", err, stdout)
	}
}
