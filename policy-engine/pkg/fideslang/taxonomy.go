package fideslang

// TaxonomyIndex provides fast lookups for taxonomy hierarchies.
type TaxonomyIndex struct {
	dataCategory map[string]*TaxonomyEntry
	dataUse      map[string]*TaxonomyEntry
	dataSubject  map[string]*TaxonomyEntry
}

// NewTaxonomyIndex creates an indexed taxonomy for efficient lookups.
func NewTaxonomyIndex(t *Taxonomy) *TaxonomyIndex {
	idx := &TaxonomyIndex{
		dataCategory: make(map[string]*TaxonomyEntry, len(t.DataCategory)),
		dataUse:      make(map[string]*TaxonomyEntry, len(t.DataUse)),
		dataSubject:  make(map[string]*TaxonomyEntry, len(t.DataSubject)),
	}
	for i := range t.DataCategory {
		idx.dataCategory[t.DataCategory[i].FidesKey] = &t.DataCategory[i]
	}
	for i := range t.DataUse {
		idx.dataUse[t.DataUse[i].FidesKey] = &t.DataUse[i]
	}
	for i := range t.DataSubject {
		idx.dataSubject[t.DataSubject[i].FidesKey] = &t.DataSubject[i]
	}
	return idx
}

// GetCategoryHierarchy returns the hierarchy from the given key to root.
// Example: "user.contact.email" -> ["user.contact.email", "user.contact", "user"]
func (idx *TaxonomyIndex) GetCategoryHierarchy(fidesKey string) []string {
	return idx.getHierarchy(fidesKey, idx.dataCategory)
}

// GetUseHierarchy returns the hierarchy from the given key to root.
func (idx *TaxonomyIndex) GetUseHierarchy(fidesKey string) []string {
	return idx.getHierarchy(fidesKey, idx.dataUse)
}

// GetSubjectHierarchy returns the hierarchy for a data subject.
// Subjects don't have a hierarchical structure, so this returns just the key.
func (idx *TaxonomyIndex) GetSubjectHierarchy(fidesKey string) []string {
	return []string{fidesKey}
}

// getHierarchy traverses the parent chain and builds the hierarchy list.
func (idx *TaxonomyIndex) getHierarchy(fidesKey string, entries map[string]*TaxonomyEntry) []string {
	hierarchy := make([]string, 0, 4)
	currentKey := fidesKey
	visited := make(map[string]bool)

	for currentKey != "" && !visited[currentKey] {
		visited[currentKey] = true
		hierarchy = append(hierarchy, currentKey)

		entry, ok := entries[currentKey]
		if !ok || entry.ParentKey == nil {
			break
		}
		currentKey = *entry.ParentKey
	}

	return hierarchy
}
