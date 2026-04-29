import { useMemo } from "react";

import type { DataPurpose, PurposeSummary } from "./data-purpose.slice";

const usePurposeCardFilters = (
  purposes: DataPurpose[],
  summaries: PurposeSummary[],
) => {
  const summariesByKey = useMemo(
    () => new Map(summaries.map((summary) => [summary.fides_key, summary])),
    [summaries],
  );

  const groups = useMemo(() => {
    const byDataUse = new Map<
      string,
      { items: DataPurpose[]; systemCount: number; datasetCount: number }
    >();
    purposes.forEach((purpose) => {
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
  }, [purposes, summariesByKey]);

  return {
    groups,
    summariesByKey,
  };
};

export default usePurposeCardFilters;
