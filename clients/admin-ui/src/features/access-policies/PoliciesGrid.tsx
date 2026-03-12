import { useMemo, useState } from "react";

import { MOCK_POLICY_CATEGORIES } from "./mock-data";
import PoliciesToolbar from "./PoliciesToolbar";
import PolicyCategoryGroup from "./PolicyCategoryGroup";
import { PolicyCategory } from "./types";

const PoliciesGrid = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [toggleStates, setToggleStates] = useState<Record<string, boolean>>(
    () => {
      const initial: Record<string, boolean> = {};
      MOCK_POLICY_CATEGORIES.forEach((cat) =>
        cat.policies.forEach((p) => {
          initial[p.id] = p.isEnabled;
        }),
      );
      return initial;
    },
  );

  const handleTogglePolicy = (id: string) => {
    setToggleStates((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const filteredCategories: PolicyCategory[] = useMemo(() => {
    if (!searchQuery.trim()) {
      return MOCK_POLICY_CATEGORIES.map((cat) => ({
        ...cat,
        policies: cat.policies.map((p) => ({
          ...p,
          isEnabled: toggleStates[p.id] ?? p.isEnabled,
        })),
      }));
    }

    const query = searchQuery.toLowerCase();
    return MOCK_POLICY_CATEGORIES.map((cat) => ({
      ...cat,
      policies: cat.policies
        .filter(
          (p) =>
            p.title.toLowerCase().includes(query) ||
            p.description.toLowerCase().includes(query),
        )
        .map((p) => ({
          ...p,
          isEnabled: toggleStates[p.id] ?? p.isEnabled,
        })),
    })).filter((cat) => cat.policies.length > 0);
  }, [searchQuery, toggleStates]);

  return (
    <div>
      <PoliciesToolbar
        searchValue={searchQuery}
        onSearchChange={setSearchQuery}
      />
      {filteredCategories.map((category) => (
        <PolicyCategoryGroup
          key={category.id}
          category={category}
          industryLabel="Fintech"
          onTogglePolicy={handleTogglePolicy}
        />
      ))}
    </div>
  );
};

export default PoliciesGrid;
