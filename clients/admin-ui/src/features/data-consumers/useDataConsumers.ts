import { useMemo, useState } from "react";

import { MOCK_DATA_CONSUMERS, UNRESOLVED_ACCESSOR_COUNT } from "./mockData";
import type { MockDataConsumer } from "./types";

export interface ConsumerMetrics {
  total: number;
  withViolations: number;
  noPurposes: number;
  aiAgents: number;
}

// When backend APIs are ready, swap internals for RTK Query hooks — no component changes needed.
export const useDataConsumers = () => {
  const [consumers] = useState<MockDataConsumer[]>(MOCK_DATA_CONSUMERS);

  const metrics = useMemo<ConsumerMetrics>(
    () => ({
      total: consumers.length,
      withViolations: consumers.filter((c) => c.violationCount > 0).length,
      noPurposes: consumers.filter((c) => c.purposes.length === 0).length,
      aiAgents: consumers.filter((c) => c.type === "ai_agent").length,
    }),
    [consumers],
  );

  return {
    consumers,
    metrics,
    unresolvedCount: UNRESOLVED_ACCESSOR_COUNT,
  };
};
