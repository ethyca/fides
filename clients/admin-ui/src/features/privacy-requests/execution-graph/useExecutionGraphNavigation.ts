import { useCallback, useEffect, useRef, useState } from "react";

export type GraphViewMode = "datasets" | "collections";

interface ExecutionGraphNavigation {
  viewMode: GraphViewMode;
  selectedDataset: string | null;
  selectDataset: (datasetName: string) => void;
  goBack: () => void;
}

const DATASET_VIEW_THRESHOLD = 30;

export function useExecutionGraphNavigation(
  totalVisibleNodes: number,
): ExecutionGraphNavigation {
  const shouldShowDatasetView = totalVisibleNodes >= DATASET_VIEW_THRESHOLD;

  const [viewMode, setViewMode] = useState<GraphViewMode>("collections");
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  const hasAutoSwitched = useRef(false);

  useEffect(() => {
    if (shouldShowDatasetView && !hasAutoSwitched.current) {
      hasAutoSwitched.current = true;
      setViewMode("datasets");
      setSelectedDataset(null);
    }
  }, [shouldShowDatasetView]);

  const selectDataset = useCallback((datasetName: string) => {
    setSelectedDataset(datasetName);
    setViewMode("collections");
  }, []);

  const goBack = useCallback(() => {
    setSelectedDataset(null);
    setViewMode("datasets");
  }, []);

  if (!shouldShowDatasetView && viewMode === "datasets") {
    return {
      viewMode: "collections",
      selectedDataset: null,
      selectDataset,
      goBack,
    };
  }

  return { viewMode, selectedDataset, selectDataset, goBack };
}
