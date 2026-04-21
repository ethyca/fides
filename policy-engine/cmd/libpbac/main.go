// Package main builds a C-shared library exposing the PBAC evaluation
// engine to Python (or any FFI-capable language) via JSON-in/JSON-out
// exported functions.
//
// Build:
//
//	go build -buildmode=c-shared -o libpbac.so ./cmd/libpbac/
//
// This produces libpbac.so (Linux), libpbac.dylib (macOS), or
// libpbac.dll (Windows) plus a libpbac.h header.
//
// All exported functions follow the same pattern:
//   - Accept a C string containing a JSON request
//   - Return a C string containing a JSON response
//   - The caller is responsible for freeing the returned C string
//     (Python ctypes handles this automatically)
//
// The JSON schemas match the sidecar HTTP endpoints exactly so the
// same payloads work for both the shared-library and HTTP paths.
package main

/*
#include <stdlib.h>
*/
import "C"

import (
	"encoding/json"
	"unsafe"

	"github.com/ethyca/fides/policy-engine/pkg/fixtures"
	"github.com/ethyca/fides/policy-engine/pkg/pbac"
	"github.com/ethyca/fides/policy-engine/pkg/pipeline"
)

// ── Pipeline evaluation ─────────────────────────────────────────────

type pipelineRequest struct {
	Fixtures pipeline.Fixtures `json:"fixtures"`
	Input    pipeline.Input    `json:"input"`
}

//export EvaluatePipelineJSON
func EvaluatePipelineJSON(input *C.char) *C.char {
	var req pipelineRequest
	if err := json.Unmarshal([]byte(C.GoString(input)), &req); err != nil {
		return jsonError(err)
	}
	record := pipeline.Evaluate(req.Fixtures, req.Input)
	return jsonResult(record)
}

// ── Purpose evaluation ──────────────────────────────────────────────

//export EvaluatePurposeJSON
func EvaluatePurposeJSON(input *C.char) *C.char {
	var req pbac.EvaluatePurposeRequest
	if err := json.Unmarshal([]byte(C.GoString(input)), &req); err != nil {
		return jsonError(err)
	}
	result := pbac.EvaluatePurpose(req.Consumer, req.Datasets, req.Collections)
	return jsonResult(result)
}

// ── Policy evaluation ───────────────────────────────────────────────

//export EvaluatePoliciesJSON
func EvaluatePoliciesJSON(input *C.char) *C.char {
	var req pbac.EvaluatePoliciesRequest
	if err := json.Unmarshal([]byte(C.GoString(input)), &req); err != nil {
		return jsonError(err)
	}
	result := pbac.EvaluatePolicies(req.Policies, &req.Request)
	return jsonResult(result)
}

// ── Fixture loading ─────────────────────────────────────────────────

type loadFixturesRequest struct {
	ConfigDir string `json:"config_dir"`
}

type loadFixturesResponse struct {
	Consumers map[string]fixtures.Consumer `json:"consumers"`
	Purposes  map[string]fixtures.Purpose  `json:"purposes"`
	Datasets  fixtures.Datasets            `json:"datasets"`
	Policies  []pbac.AccessPolicy          `json:"policies"`
	Error     string                       `json:"error,omitempty"`
}

//export LoadFixturesJSON
func LoadFixturesJSON(input *C.char) *C.char {
	var req loadFixturesRequest
	if err := json.Unmarshal([]byte(C.GoString(input)), &req); err != nil {
		return jsonError(err)
	}
	consumers, err := fixtures.LoadConsumers(req.ConfigDir + "/consumers")
	if err != nil {
		return jsonError(err)
	}
	purposes, err := fixtures.LoadPurposes(req.ConfigDir + "/purposes")
	if err != nil {
		return jsonError(err)
	}
	datasets, err := fixtures.LoadDatasets(req.ConfigDir + "/datasets")
	if err != nil {
		return jsonError(err)
	}
	policies, err := fixtures.LoadPolicies(req.ConfigDir + "/policies")
	if err != nil {
		return jsonError(err)
	}
	return jsonResult(loadFixturesResponse{
		Consumers: consumers,
		Purposes:  purposes,
		Datasets:  datasets,
		Policies:  policies,
	})
}

// ── Memory management ───────────────────────────────────────────────

//export FreeString
func FreeString(s *C.char) {
	C.free(unsafe.Pointer(s))
}

// ── Helpers ─────────────────────────────────────────────────────────

func jsonResult(v interface{}) *C.char {
	b, err := json.Marshal(v)
	if err != nil {
		return jsonError(err)
	}
	return C.CString(string(b))
}

func jsonError(err error) *C.char {
	b, _ := json.Marshal(map[string]string{"error": err.Error()})
	return C.CString(string(b))
}

func main() {} // required for c-shared build mode
