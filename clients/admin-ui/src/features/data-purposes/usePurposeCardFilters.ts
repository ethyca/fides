import { useMemo, useState } from "react";

import type { DataPurpose, PurposeSummary } from "./data-purpose.slice";
import { computeCategoryDrift, formatDataUse } from "./purposeUtils";

const usePurposeCardFilters = (
  purposes: DataPurpose[],
  summaries: PurposeSummary[],
) => {
  const [consumerFilter, setConsumerFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);

  const summariesByKey = useMemo(
    () => new Map(summaries.map((summary) => [summary.fides_key, summary])),
    [summaries],
  );

  const consumerOptions = useMemo(() => {
    const seenSystemIds = new Set<string>();
    const options: { value: string; label: string }[] = [];
    summaries.forEach((summary) => {
      summary.systems
        .filter((assignment) => assignment.assigned)
        .forEach((assignment) => {
          if (!seenSystemIds.has(assignment.system_id)) {
            seenSystemIds.add(assignment.system_id);
            options.push({
              value: assignment.system_id,
              label: assignment.system_name,
            });
          }
        });
    });
    return options.sort((left, right) => left.label.localeCompare(right.label));
  }, [summaries]);

  const dataUseOptions = useMemo(
    () =>
      [...new Set(purposes.map((purpose) => purpose.data_use))].map(
        (dataUse) => ({
          value: dataUse,
          label: formatDataUse(dataUse),
        }),
      ),
    [purposes],
  );

  const categoryOptions = useMemo(() => {
    const allCategories = new Set<string>();
    purposes.forEach((purpose) =>
      (purpose.data_categories ?? []).forEach((category) =>
        allCategories.add(category),
      ),
    );
    return Array.from(allCategories)
      .sort()
      .map((category) => ({ value: category, label: category }));
  }, [purposes]);

  const filtered = useMemo(() => {
    return purposes.filter((purpose) => {
      if (
        categoryFilter &&
        !(purpose.data_categories ?? []).includes(categoryFilter)
      ) {
        return false;
      }
      if (!consumerFilter && !statusFilter) {
        return true;
      }
      const summary = summariesByKey.get(purpose.fides_key);
      if (
        consumerFilter &&
        !summary?.systems.some(
          (assignment) =>
            assignment.assigned && assignment.system_id === consumerFilter,
        )
      ) {
        return false;
      }
      if (statusFilter) {
        const { status } = computeCategoryDrift(
          purpose.data_categories ?? [],
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
    filtered.forEach((purpose) => {
      const summary = summariesByKey.get(purpose.fides_key);
      const group = byDataUse.get(purpose.data_use) ?? {
        items: [],
        systemCount: 0,
        datasetCount: 0,
      };
      group.items.push(purpose);
      group.systemCount += summary?.system_count ?? 0;
      group.datasetCount += summary?.dataset_count ?? 0;
      byDataUse.set(purpose.data_use, group);
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
