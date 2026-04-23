import { useMemo, useState } from "react";

import type { DataPurpose, PurposeSummary } from "./data-purpose.slice";
import { computeCategoryDrift, formatDataUse } from "./purposeUtils";

/**
 * Filter + grouping logic for the purpose card grid.
 *
 * `search` and `data_use` are applied server-side by `usePurposesList`, so
 * they aren't owned here. The remaining filters (`consumer`, `status`,
 * `data_category`) depend on summaries data that is still mock-served; move
 * them server-side once the real `summaries` endpoint lands and the list
 * endpoint accepts the corresponding params.
 */
const usePurposeCardFilters = (
  purposes: DataPurpose[],
  summaries: PurposeSummary[],
) => {
  const [consumerFilter, setConsumerFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);

  const summariesByKey = useMemo(
    () => new Map(summaries.map((s) => [s.fides_key, s])),
    [summaries],
  );

  const consumerOptions = useMemo(() => {
    const seen = new Set<string>();
    const options: { value: string; label: string }[] = [];
    summaries.forEach((summary) => {
      summary.systems
        .filter((a) => a.assigned)
        .forEach((a) => {
          if (!seen.has(a.system_id)) {
            seen.add(a.system_id);
            options.push({ value: a.system_id, label: a.system_name });
          }
        });
    });
    return options.sort((a, b) => a.label.localeCompare(b.label));
  }, [summaries]);

  const dataUseOptions = useMemo(
    () =>
      [...new Set(purposes.map((p) => p.data_use))].map((du) => ({
        value: du,
        label: formatDataUse(du),
      })),
    [purposes],
  );

  const categoryOptions = useMemo(() => {
    const all = new Set<string>();
    purposes.forEach((p) =>
      (p.data_categories ?? []).forEach((c) => all.add(c)),
    );
    return Array.from(all)
      .sort()
      .map((c) => ({ value: c, label: c }));
  }, [purposes]);

  const filtered = useMemo(() => {
    return purposes.filter((p) => {
      if (
        categoryFilter &&
        !(p.data_categories ?? []).includes(categoryFilter)
      ) {
        return false;
      }
      if (!consumerFilter && !statusFilter) {
        return true;
      }
      const summary = summariesByKey.get(p.fides_key);
      if (
        consumerFilter &&
        !summary?.systems.some(
          (a) => a.assigned && a.system_id === consumerFilter,
        )
      ) {
        return false;
      }
      if (statusFilter) {
        const { status } = computeCategoryDrift(
          p.data_categories ?? [],
          summary?.detected_data_categories ?? [],
        );
        if (status !== statusFilter) {
          return false;
        }
      }
      return true;
    });
  }, [purposes, summariesByKey, consumerFilter, statusFilter, categoryFilter]);

  const groups = useMemo(() => {
    const byDataUse = new Map<
      string,
      { items: DataPurpose[]; systemCount: number; datasetCount: number }
    >();
    filtered.forEach((p) => {
      const summary = summariesByKey.get(p.fides_key);
      const group = byDataUse.get(p.data_use) ?? {
        items: [],
        systemCount: 0,
        datasetCount: 0,
      };
      group.items.push(p);
      group.systemCount += summary?.system_count ?? 0;
      group.datasetCount += summary?.dataset_count ?? 0;
      byDataUse.set(p.data_use, group);
    });
    return Array.from(byDataUse, ([dataUse, group]) => ({ dataUse, ...group }));
  }, [filtered, summariesByKey]);

  const hasActiveFilters = Boolean(
    consumerFilter || statusFilter || categoryFilter,
  );

  const clearFilters = () => {
    setConsumerFilter(null);
    setStatusFilter(null);
    setCategoryFilter(null);
  };

  return {
    consumerFilter,
    setConsumerFilter,
    statusFilter,
    setStatusFilter,
    categoryFilter,
    setCategoryFilter,
    consumerOptions,
    dataUseOptions,
    categoryOptions,
    filtered,
    groups,
    summariesByKey,
    hasActiveFilters,
    clearFilters,
  };
};

export default usePurposeCardFilters;
