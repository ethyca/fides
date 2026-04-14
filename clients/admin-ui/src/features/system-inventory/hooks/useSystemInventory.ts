import { useMemo, useState } from "react";

import { MOCK_SYSTEMS } from "../mock-data";
import {
  type GovernanceHealthData,
  HealthStatus,
  RiskFreshness,
  RiskSeverity,
  type SystemInventoryStats,
} from "../types";
import {
  computeGovernanceHealth,
  getRiskFreshness,
  latestRiskTimestamp,
} from "../utils";

export const useSystemInventory = () => {
  const [search, setSearch] = useState("");
  const [healthFilter, setHealthFilter] = useState<HealthStatus | null>(null);
  const [severityFilter, setSeverityFilter] = useState<RiskSeverity[]>([]);
  const [freshnessFilter, setFreshnessFilter] = useState<RiskFreshness | null>(
    null,
  );
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

    if (severityFilter.length > 0) {
      result = result.filter((s) =>
        s.risks.some((r) => severityFilter.includes(r.severity)),
      );
    }

    if (freshnessFilter) {
      result = result.filter((s) =>
        s.risks.some((r) => getRiskFreshness(r.detectedAt) === freshnessFilter),
      );
    }

    if (typeFilter) {
      result = result.filter((s) => s.system_type === typeFilter);
    }

    if (groupFilter) {
      result = result.filter((s) => s.group === groupFilter);
    }

    // Default sort by name; specific sections re-sort below.
    return [...result].sort((a, b) => a.name.localeCompare(b.name));
  }, [
    systems,
    search,
    healthFilter,
    severityFilter,
    freshnessFilter,
    typeFilter,
    groupFilter,
  ]);

  const stats: SystemInventoryStats = useMemo(
    () => ({
      total: systems.length,
      violations: 0,
      risks: systems.filter((s) => s.risk_count > 0).length,
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
        .sort((a, b) => {
          if (b.risk_count !== a.risk_count) {
            return b.risk_count - a.risk_count;
          }
          return latestRiskTimestamp(b.risks) - latestRiskTimestamp(a.risks);
        }),
    [filtered],
  );

  const healthy = useMemo(
    () =>
      filtered
        .filter((s) => s.health === HealthStatus.HEALTHY)
        .sort(
          (a, b) =>
            latestRiskTimestamp(b.risks) - latestRiskTimestamp(a.risks) ||
            a.name.localeCompare(b.name),
        ),
    [filtered],
  );

  const typeOptions = useMemo(() => {
    const types = [...new Set(systems.map((s) => s.system_type))].sort();
    return types.map((t) => ({ label: t, value: t }));
  }, [systems]);

  const groupOptions = useMemo(() => {
    const groups = [
      ...new Set(systems.map((s) => s.group).filter(Boolean)),
    ].sort() as string[];
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
    severityFilter,
    setSeverityFilter,
    freshnessFilter,
    setFreshnessFilter,
    typeFilter,
    setTypeFilter,
    groupFilter,
    setGroupFilter,
    typeOptions,
    groupOptions,
  };
};
