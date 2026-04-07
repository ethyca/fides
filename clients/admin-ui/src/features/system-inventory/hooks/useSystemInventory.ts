import { useMemo, useState } from "react";

import { MOCK_SYSTEMS } from "../mock-data";
import { HealthStatus, type GovernanceHealthData, type SystemInventoryStats } from "../types";
import { computeGovernanceHealth } from "../utils";

export const useSystemInventory = () => {
  const [search, setSearch] = useState("");
  const [healthFilter, setHealthFilter] = useState<HealthStatus | null>(null);
  const [purposeFilter, setPurposeFilter] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [groupFilter, setGroupFilter] = useState<string | null>(null);

  const systems = MOCK_SYSTEMS;

  const filtered = useMemo(() => {
    let result = systems;

    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (s) =>
          s.name.toLowerCase().includes(q) ||
          s.system_type.toLowerCase().includes(q),
      );
    }

    if (healthFilter) {
      result = result.filter((s) => s.health === healthFilter);
    }

    if (purposeFilter) {
      result = result.filter((s) =>
        s.purposes.some((p) => p.name === purposeFilter),
      );
    }

    if (typeFilter) {
      result = result.filter((s) => s.system_type === typeFilter);
    }

    if (groupFilter) {
      result = result.filter((s) => s.group === groupFilter);
    }

    return [...result].sort((a, b) => a.name.localeCompare(b.name));
  }, [systems, search, healthFilter, purposeFilter, typeFilter, groupFilter]);

  const stats: SystemInventoryStats = useMemo(
    () => ({
      total: systems.length,
      violations: 0,
      issues: systems.filter((s) => s.health === HealthStatus.ISSUES).length,
      healthy: systems.filter((s) => s.health === HealthStatus.HEALTHY).length,
    }),
    [systems],
  );

  const governanceHealth: GovernanceHealthData = useMemo(
    () => computeGovernanceHealth(systems),
    [systems],
  );

  const needsAttention = useMemo(
    () =>
      filtered
        .filter((s) => s.health !== HealthStatus.HEALTHY)
        .sort((a, b) => b.issue_count - a.issue_count),
    [filtered],
  );

  const healthy = useMemo(
    () => filtered.filter((s) => s.health === HealthStatus.HEALTHY),
    [filtered],
  );

  const purposeOptions = useMemo(() => {
    const names = new Set<string>();
    systems.forEach((s) => s.purposes.forEach((p) => names.add(p.name)));
    return [...names].sort().map((n) => ({ label: n, value: n }));
  }, [systems]);

  const typeOptions = useMemo(() => {
    const types = [...new Set(systems.map((s) => s.system_type))].sort();
    return types.map((t) => ({ label: t, value: t }));
  }, [systems]);

  const groupOptions = useMemo(() => {
    const groups = [...new Set(systems.map((s) => s.group).filter(Boolean))].sort() as string[];
    return groups.map((g) => ({ label: g, value: g }));
  }, [systems]);

  return {
    systems: filtered,
    needsAttention,
    healthy,
    governanceHealth,
    stats,
    search,
    setSearch,
    healthFilter,
    setHealthFilter,
    purposeFilter,
    setPurposeFilter,
    typeFilter,
    setTypeFilter,
    groupFilter,
    setGroupFilter,
    purposeOptions,
    typeOptions,
    groupOptions,
  };
};
