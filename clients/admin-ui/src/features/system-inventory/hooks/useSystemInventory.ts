import type { Dayjs } from "dayjs";
import { useMemo, useState } from "react";

import { MOCK_SYSTEMS } from "../mock-data";
import {
  type GovernanceHealthData,
  HealthStatus,
  RiskSeverity,
  type SystemInventoryStats,
} from "../types";
import { computeGovernanceHealth, latestRiskTimestamp } from "../utils";

export const useSystemInventory = () => {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<
    (RiskSeverity | HealthStatus)[]
  >([]);
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null);
  const [stewardFilter, setStewardFilter] = useState<string | null>(
    "Jack Gale",
  );
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

    if (statusFilter.length > 0) {
      const healthValues = statusFilter.filter(
        (v): v is HealthStatus =>
          v === HealthStatus.HEALTHY || v === HealthStatus.ISSUES,
      );
      const severityValues = statusFilter.filter(
        (v): v is RiskSeverity => !healthValues.includes(v as HealthStatus),
      );

      result = result.filter((s) => {
        const matchesHealth =
          healthValues.length === 0 || healthValues.includes(s.health);
        const matchesSeverity =
          severityValues.length === 0 ||
          s.risks.some((r) => severityValues.includes(r.severity));
        return matchesHealth && matchesSeverity;
      });
    }

    if (dateRange) {
      const [start, end] = dateRange;
      const startMs = start.startOf("day").valueOf();
      const endMs = end.endOf("day").valueOf();
      result = result.filter((s) =>
        s.risks.some((r) => {
          const ts = new Date(r.detectedAt).getTime();
          return ts >= startMs && ts <= endMs;
        }),
      );
    }

    if (stewardFilter) {
      result = result.filter((s) =>
        s.stewards.some((st) => st.name === stewardFilter),
      );
    }

    if (groupFilter) {
      result = result.filter((s) => s.group === groupFilter);
    }

    // Default sort by name; specific sections re-sort below.
    return [...result].sort((a, b) => a.name.localeCompare(b.name));
  }, [
    systems,
    search,
    statusFilter,
    dateRange,
    stewardFilter,
    groupFilter,
  ]);

  const stats: SystemInventoryStats = useMemo(
    () => ({
      total: filtered.length,
      violations: 0,
      risks: filtered.filter((s) => s.risk_count > 0).length,
      healthy: filtered.filter((s) => s.health === HealthStatus.HEALTHY).length,
    }),
    [filtered],
  );

  const governanceHealth: GovernanceHealthData = useMemo(
    () => computeGovernanceHealth(filtered),
    [filtered],
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

  const stewardOptions = useMemo(() => {
    const names = new Set<string>();
    systems.forEach((s) => s.stewards.forEach((st) => names.add(st.name)));
    return [...names].sort().map((n) => ({ label: n, value: n }));
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
    statusFilter,
    setStatusFilter,
    dateRange,
    setDateRange,
    stewardFilter,
    setStewardFilter,
    groupFilter,
    setGroupFilter,
    stewardOptions,
    groupOptions,
  };
};
