import { useMemo } from "react";

import { ProgressCard } from "~/features/data-discovery-and-detection/action-center/ProgressCard/ProgressCard";

import { getCompleteness } from "./purposeUtils";
import type { DataPurpose, PurposeSummary } from "./types";

interface PurposeSummaryRowProps {
  purposes: DataPurpose[];
  summaries: PurposeSummary[];
}

const PurposeSummaryRow = ({ purposes, summaries }: PurposeSummaryRowProps) => {
  const totalSystems = useMemo(
    () => summaries.reduce((sum, s) => sum + s.system_count, 0),
    [summaries],
  );

  const totalDatasets = useMemo(
    () => summaries.reduce((sum, s) => sum + s.dataset_count, 0),
    [summaries],
  );

  const avgCompleteness = useMemo(() => {
    if (purposes.length === 0) return 0;
    const total = purposes.reduce((sum, p) => sum + getCompleteness(p), 0);
    return Math.round(total / purposes.length);
  }, [purposes]);

  const categoryBreakdown = useMemo(() => {
    const counts: Record<string, number> = {};
    purposes.forEach((p) => {
      counts[p.data_use] = (counts[p.data_use] || 0) + 1;
    });
    return Object.entries(counts).map(([label, count]) => ({
      label,
      value: Math.round((count / purposes.length) * 100),
    }));
  }, [purposes]);

  return (
    <ProgressCard
      title="Data Purposes"
      subtitle={`${purposes.length} purposes`}
      compact
      progress={{
        label: "Avg. completeness",
        percent: avgCompleteness,
        numerator: purposes.filter((p) => getCompleteness(p) >= 80).length,
        denominator: purposes.length,
      }}
      numericStats={{
        label: "Coverage",
        data: [
          { label: "purposes", count: purposes.length },
          { label: "data consumers", count: totalSystems },
          { label: "datasets", count: totalDatasets },
        ],
      }}
      percentageStats={{
        label: "Categories",
        data: categoryBreakdown,
      }}
    />
  );
};

export default PurposeSummaryRow;
