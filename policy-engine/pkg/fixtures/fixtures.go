// Package fixtures loads PBAC YAML config directories into shapes the
// engine can consume.
//
// The directory layout matches pbac/ at the repo root:
//
//	<config>/consumers/*.yml   top-level key: consumer:
//	<config>/purposes/*.yml    top-level key: purpose:
//	<config>/datasets/*.yml    fideslang Dataset YAML, top-level key: dataset:
//	<config>/policies/*.yml    top-level key: policy:
package fixtures

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/ethyca/fides/policy-engine/pkg/pbac"
	"gopkg.in/yaml.v3"
)

// Consumer is a data consumer loaded from YAML. Members is the list of
// identities (typically email addresses) that resolve to this consumer.
type Consumer struct {
	Name        string   `yaml:"name" json:"name"`
	Description string   `yaml:"description,omitempty" json:"description,omitempty"`
	Members     []string `yaml:"members" json:"members"`
	Purposes    []string `yaml:"purposes" json:"purposes"`
}

type consumerFile struct {
	Consumer []Consumer `yaml:"consumer"`
}

// Purpose is a declared purpose loaded from YAML.
type Purpose struct {
	FidesKey       string   `yaml:"fides_key" json:"fides_key"`
	Name           string   `yaml:"name" json:"name"`
	DataUse        string   `yaml:"data_use" json:"data_use"`
	DataSubject    string   `yaml:"data_subject,omitempty" json:"data_subject,omitempty"`
	DataCategories []string `yaml:"data_categories,omitempty" json:"data_categories,omitempty"`
	Description    string   `yaml:"description,omitempty" json:"description,omitempty"`
}

type purposeFile struct {
	Purpose []Purpose `yaml:"purpose"`
}

// dataset / collection / field carry data_purposes at each level. The
// engine reads dataset-level purposes directly and reads collection
// purposes via DatasetPurposes.CollectionPurposes. Field purposes are
// unioned into their owning collection's CollectionPurposes since the
// CLI extracts tables (collections) from SQL, not individual columns.
type dataset struct {
	FidesKey     string       `yaml:"fides_key"`
	Name         string       `yaml:"name,omitempty"`
	DataPurposes []string     `yaml:"data_purposes,omitempty"`
	Collections  []collection `yaml:"collections,omitempty"`
}

type collection struct {
	Name         string   `yaml:"name"`
	DataPurposes []string `yaml:"data_purposes,omitempty"`
	Fields       []field  `yaml:"fields,omitempty"`
}

type field struct {
	Name         string   `yaml:"name"`
	DataPurposes []string `yaml:"data_purposes,omitempty"`
}

type datasetFile struct {
	Dataset []dataset `yaml:"dataset"`
}

// Datasets bundles everything LoadDatasets returns: the per-dataset
// purpose map (engine input) and the table-name -> dataset_key index
// (table resolution).
type Datasets struct {
	// Purposes is keyed by dataset fides_key and fed to the engine.
	Purposes map[string]pbac.DatasetPurposes `json:"purposes"`
	// Tables maps a lowercase table name to its owning dataset's
	// fides_key. Assumes table names are globally unique across
	// datasets; on collision the last one loaded wins.
	Tables map[string]string `json:"tables"`
}

// LoadConsumers walks dir for *.yml files and returns a map from member
// identity to Consumer. A consumer with N members appears N times in the
// map, once per member, all pointing to the same Consumer value.
//
// When two consumers list the same member, the last one loaded wins.
// Returns an empty map (not an error) if dir doesn't exist.
func LoadConsumers(dir string) (map[string]Consumer, error) {
	out := map[string]Consumer{}
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		return out, nil
	}
	matches, err := filepath.Glob(filepath.Join(dir, "*.yml"))
	if err != nil {
		return nil, err
	}
	for _, path := range matches {
		var f consumerFile
		if err := readYAML(path, &f); err != nil {
			return nil, fmt.Errorf("consumers: %s: %w", path, err)
		}
		for _, c := range f.Consumer {
			for _, member := range c.Members {
				if member != "" {
					out[member] = c
				}
			}
		}
	}
	return out, nil
}

// LoadPurposes walks dir for *.yml files and returns a map keyed by FidesKey.
func LoadPurposes(dir string) (map[string]Purpose, error) {
	out := map[string]Purpose{}
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		return out, nil
	}
	matches, err := filepath.Glob(filepath.Join(dir, "*.yml"))
	if err != nil {
		return nil, err
	}
	for _, path := range matches {
		var f purposeFile
		if err := readYAML(path, &f); err != nil {
			return nil, fmt.Errorf("purposes: %s: %w", path, err)
		}
		for _, p := range f.Purpose {
			if p.FidesKey != "" {
				out[p.FidesKey] = p
			}
		}
	}
	return out, nil
}

// LoadDatasets walks dir for fideslang Dataset YAML files and returns
// both the per-dataset purpose map (for the engine) and a table ->
// dataset_key index built from collections[].name.
//
// Table resolution assumes collection names are globally unique across
// datasets, so SELECT ... FROM warehouse.orders and
// SELECT ... FROM archive.orders both resolve to whichever dataset
// declares a collection named "orders".
//
// Purposes are unioned across the three taxonomy levels:
//
//   - dataset.data_purposes                 → DatasetPurposes.PurposeKeys
//   - collection.data_purposes              ┐
//   - union(field.data_purposes for fields) ┴ → CollectionPurposes[name]
//
// The engine's EffectivePurposes(collection) then unions PurposeKeys
// with CollectionPurposes[collection], so the final effective set for
// a query on <dataset>.<collection> is the union of all three levels.
func LoadDatasets(dir string) (Datasets, error) {
	result := Datasets{
		Purposes: map[string]pbac.DatasetPurposes{},
		Tables:   map[string]string{},
	}
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		return result, nil
	}
	matches, err := filepath.Glob(filepath.Join(dir, "*.yml"))
	if err != nil {
		return result, err
	}
	for _, path := range matches {
		var f datasetFile
		if err := readYAML(path, &f); err != nil {
			return result, fmt.Errorf("datasets: %s: %w", path, err)
		}
		for _, ds := range f.Dataset {
			if ds.FidesKey == "" {
				continue
			}
			dp := pbac.DatasetPurposes{
				DatasetKey:         ds.FidesKey,
				PurposeKeys:        ds.DataPurposes,
				CollectionPurposes: map[string][]string{},
			}
			for _, c := range ds.Collections {
				if c.Name == "" {
					continue
				}
				name := strings.ToLower(c.Name)
				effective := collectionEffectivePurposes(c)
				if len(effective) > 0 {
					dp.CollectionPurposes[name] = effective
				}
				result.Tables[name] = ds.FidesKey
			}
			result.Purposes[ds.FidesKey] = dp
		}
	}
	return result, nil
}

// collectionEffectivePurposes unions a collection's own data_purposes
// with every one of its fields' data_purposes. Result is deduplicated
// and sorted for deterministic output.
func collectionEffectivePurposes(c collection) []string {
	set := map[string]bool{}
	for _, p := range c.DataPurposes {
		if p != "" {
			set[p] = true
		}
	}
	for _, fd := range c.Fields {
		for _, p := range fd.DataPurposes {
			if p != "" {
				set[p] = true
			}
		}
	}
	if len(set) == 0 {
		return nil
	}
	out := make([]string, 0, len(set))
	for p := range set {
		out = append(out, p)
	}
	sort.Strings(out)
	return out
}

type policyFile struct {
	Policy []pbac.AccessPolicy `yaml:"policy"`
}

// LoadPolicies walks dir for *.yml files and returns the enabled access
// policies. Disabled policies (enabled: false) are filtered out so the
// CLI doesn't have to care about the enabled flag later.
//
// Returns an empty slice (not an error) if dir doesn't exist.
func LoadPolicies(dir string) ([]pbac.AccessPolicy, error) {
	out := []pbac.AccessPolicy{}
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		return out, nil
	}
	matches, err := filepath.Glob(filepath.Join(dir, "*.yml"))
	if err != nil {
		return nil, err
	}
	for _, path := range matches {
		var f policyFile
		if err := readYAML(path, &f); err != nil {
			return nil, fmt.Errorf("policies: %s: %w", path, err)
		}
		for _, p := range f.Policy {
			if p.Enabled != nil && !*p.Enabled {
				continue
			}
			out = append(out, p)
		}
	}
	return out, nil
}

func readYAML(path string, into interface{}) error {
	b, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	return yaml.Unmarshal(b, into)
}
