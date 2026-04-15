import { useCallback, useMemo, useState } from "react";

import { MOCK_COVERAGE, MOCK_DATASET_ASSIGNMENTS, MOCK_PURPOSES, MOCK_SYSTEM_ASSIGNMENTS } from "./mockData";
import type {
  DataPurpose,
  PurposeCoverage,
  PurposeDatasetAssignment,
  PurposeSummary,
  PurposeSystemAssignment,
} from "./types";

/**
 * Hook wrapping mock data for the data purposes feature.
 * When backend APIs are ready, swap internals for RTK Query hooks —
 * no component changes needed.
 */
export const usePurposes = () => {
  const [purposes, setPurposes] = useState<DataPurpose[]>(MOCK_PURPOSES);

  const getSummaries = useMemo(
    (): PurposeSummary[] =>
      purposes.map((p) => {
        const assignments = MOCK_SYSTEM_ASSIGNMENTS[p.id] ?? [];
        return {
          id: p.id,
          name: p.name,
          system_count: assignments.filter((a) => a.assigned).length,
          dataset_count: MOCK_COVERAGE[p.id]?.datasets.assigned ?? 0,
          badge_count: p.sub_types.length,
        };
      }),
    [purposes],
  );

  const getPurpose = useCallback(
    (id: string): DataPurpose | null =>
      purposes.find((p) => p.id === id) ?? null,
    [purposes],
  );

  const getCoverage = useCallback(
    (id: string): PurposeCoverage | null => MOCK_COVERAGE[id] ?? null,
    [],
  );

  const getAssignments = useCallback(
    (id: string): PurposeSystemAssignment[] =>
      MOCK_SYSTEM_ASSIGNMENTS[id] ?? [],
    [],
  );

  const getDatasetAssignments = useCallback(
    (id: string): PurposeDatasetAssignment[] =>
      MOCK_DATASET_ASSIGNMENTS[id] ?? [],
    [],
  );

  const createPurpose = useCallback(
    (values: Omit<DataPurpose, "id">) => {
      const newPurpose: DataPurpose = {
        ...values,
        id: values.key,
      };
      setPurposes((prev) => [...prev, newPurpose]);
    },
    [],
  );

  const updatePurpose = useCallback(
    (id: string, values: Partial<DataPurpose>) => {
      setPurposes((prev) =>
        prev.map((p) => (p.id === id ? { ...p, ...values } : p)),
      );
    },
    [],
  );

  return {
    purposes,
    getSummaries,
    getPurpose,
    getCoverage,
    getAssignments,
    getDatasetAssignments,
    createPurpose,
    updatePurpose,
  };
};
