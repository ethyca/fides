import { useMemo } from "react";

import { useGetControlGroupsQuery } from "./access-policies.slice";
import { useAccessPoliciesList } from "./hooks/useAccessPoliciesList";
import { useAccessPolicyGroups } from "./hooks/useAccessPolicyGroups";
import { usePoliciesFilters } from "./hooks/usePoliciesFilters";
import { useReorderPolicies } from "./hooks/useReorderPolicies";
import { useTogglePolicyEnabled } from "./hooks/useTogglePolicyEnabled";
import { useUpdatePolicyPriority } from "./hooks/useUpdatePolicyPriority";
import PoliciesGrid from "./PoliciesGrid";
import PoliciesTable from "./PoliciesTable";
import PoliciesToolbar from "./PoliciesToolbar";

const PoliciesContainer = () => {
  const { policies, isLoading } = useAccessPoliciesList();
  const { data: controlGroups } = useGetControlGroupsQuery();
  const toggleEnabled = useTogglePolicyEnabled();
  const reorderPolicies = useReorderPolicies();
  const updatePriority = useUpdatePolicyPriority();
  const {
    searchQuery,
    setSearchQuery,
    controlFilter,
    setControlFilter,
    enabledFilter,
    setEnabledFilter,
    viewMode,
    setViewMode,
  } = usePoliciesFilters();

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
          onTogglePolicy={toggleEnabled}
          isLoading={isLoading}
        />
      ) : (
        <PoliciesTable
          policies={filteredPolicies}
          controlGroups={controlGroups ?? []}
          onToggle={toggleEnabled}
          onReorder={reorderPolicies}
          onPriorityEdit={updatePriority}
          isLoading={isLoading}
        />
      )}
    </div>
  );
};

export default PoliciesContainer;
