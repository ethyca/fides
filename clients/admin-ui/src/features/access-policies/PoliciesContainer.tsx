import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import { useGetControlGroupsQuery } from "./access-policies.slice";
import {
  useAccessPoliciesList,
  useAccessPolicyGroups,
  useReorderPolicies,
  useTogglePolicyEnabled,
} from "./hooks";
import PoliciesGrid from "./PoliciesGrid";
import PoliciesTable from "./PoliciesTable";
import PoliciesToolbar, { ViewMode } from "./PoliciesToolbar";

const PoliciesContainer = () => {
  const router = useRouter();
  const { policies, isLoading } = useAccessPoliciesList();
  const { data: controlGroups } = useGetControlGroupsQuery();
  const toggleEnabled = useTogglePolicyEnabled();
  const reorderPolicies = useReorderPolicies();

  const viewMode: ViewMode = router.query.view === "table" ? "table" : "cards";

  const setViewMode = (mode: ViewMode) => {
    router.replace({ query: { ...router.query, view: mode } }, undefined, {
      shallow: true,
    });
  };
  const [searchQuery, setSearchQuery] = useState("");
  const [controlFilter, setControlFilter] = useState<string | undefined>();
  const [enabledFilter, setEnabledFilter] = useState<string | undefined>();

  // Client-side filtering
  const filteredPolicies = useMemo(() => {
    let result = policies;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          (p.description?.toLowerCase().includes(q) ?? false),
      );
    }

    if (controlFilter) {
      result = result.filter((p) => p.controls?.includes(controlFilter));
    }

    if (enabledFilter === "enabled") {
      result = result.filter((p) => p.enabled);
    } else if (enabledFilter === "disabled") {
      result = result.filter((p) => !p.enabled);
    }

    return result;
  }, [policies, searchQuery, controlFilter, enabledFilter]);

  const groups = useAccessPolicyGroups(filteredPolicies, controlGroups);

  return (
    <div>
      <PoliciesToolbar
        searchValue={searchQuery}
        onSearchChange={setSearchQuery}
        controlGroups={controlGroups ?? []}
        controlFilter={controlFilter}
        onControlFilterChange={setControlFilter}
        enabledFilter={enabledFilter}
        onEnabledFilterChange={setEnabledFilter}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
      />
      {viewMode === "cards" ? (
        <PoliciesGrid
          groups={groups}
          controlGroups={controlGroups ?? []}
          onTogglePolicy={toggleEnabled}
          isLoading={isLoading}
        />
      ) : (
        <PoliciesTable
          policies={filteredPolicies}
          controlGroups={controlGroups ?? []}
          onToggle={toggleEnabled}
          onReorder={reorderPolicies}
          isLoading={isLoading}
        />
      )}
    </div>
  );
};

export default PoliciesContainer;
