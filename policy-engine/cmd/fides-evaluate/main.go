// fides-evaluate is a CLI tool for running the Fides PBAC evaluation engine.
//
// Usage:
//
//	echo '{"consumer": {...}, "datasets": {...}}' | fides-evaluate purpose
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"

	"github.com/ethyca/fides/policy-engine/pkg/pbac"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintf(os.Stderr, "Usage: fides-evaluate <purpose> [file]\n")
		os.Exit(1)
	}

	command := os.Args[1]

	var reader io.Reader = os.Stdin
	if len(os.Args) > 2 {
		f, err := os.Open(os.Args[2])
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error opening file: %v\n", err)
			os.Exit(1)
		}
		defer f.Close()
		reader = f
	}

	input, err := io.ReadAll(reader)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error reading input: %v\n", err)
		os.Exit(1)
	}

	switch command {
	case "purpose":
		var req pbac.EvaluatePurposeRequest
		if err := json.Unmarshal(input, &req); err != nil {
			fmt.Fprintf(os.Stderr, "Error parsing JSON: %v\n", err)
			os.Exit(1)
		}
		result := pbac.EvaluatePurpose(req.Consumer, req.Datasets, req.Collections)
		writeJSON(result)

	default:
		fmt.Fprintf(os.Stderr, "Unknown command: %s\nUse 'purpose'\n", command)
		os.Exit(1)
	}
}

func writeJSON(v interface{}) {
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	if err := enc.Encode(v); err != nil {
		fmt.Fprintf(os.Stderr, "Error encoding JSON: %v\n", err)
		os.Exit(1)
	}
}
