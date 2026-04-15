import { Flex, useMessage } from "fidesui";
import { useCallback, useState } from "react";

import AssignedDatasetsSection from "./AssignedDatasetsSection";
import AssignedSystemsSection from "./AssignedSystemsSection";
import PurposeGovernanceAlert from "./PurposeGovernanceAlert";
import type {
  DataPurpose,
  PurposeCoverage,
  PurposeDatasetAssignment,
  PurposeSystemAssignment,
} from "./types";

interface PurposeDashboardProps {
  purpose: DataPurpose;
  coverage: PurposeCoverage;
  systems: PurposeSystemAssignment[];
  datasets: PurposeDatasetAssignment[];
}

const PurposeDashboard = ({
  purpose: initialPurpose,
  systems: initialSystems,
  datasets: initialDatasets,
}: PurposeDashboardProps) => {
  const message = useMessage();
  const [purpose, setPurpose] = useState<DataPurpose>(initialPurpose);
  const [systems, setSystems] =
    useState<PurposeSystemAssignment[]>(initialSystems);
  const [datasets, setDatasets] =
    useState<PurposeDatasetAssignment[]>(initialDatasets);

  const handleAcceptCategories = useCallback(
    (categories: string[]) => {
      if (categories.length === 0) return;
      setPurpose((p) => {
        const existing = new Set(p.data_categories);
        const toAdd = categories.filter((c) => !existing.has(c));
        if (toAdd.length === 0) return p;
        return {
          ...p,
          data_categories: [...p.data_categories, ...toAdd],
        };
      });
      message.success(
        categories.length === 1
          ? `Added "${categories[0]}" to defined categories`
          : `Added ${categories.length} categories to defined list`,
      );
    },
    [message],
  );

  const handleMarkMisclassified = useCallback(
    (datasetKeys: string[], categories: string[]) => {
      if (categories.length === 0) return;
      const catSet = new Set(categories);
      const keySet = new Set(datasetKeys);
      setDatasets((ds) =>
        ds.map((d) =>
          keySet.has(d.dataset_fides_key)
            ? {
                ...d,
                data_categories: d.data_categories.filter(
                  (c) => !catSet.has(c),
                ),
              }
            : d,
        ),
      );
      setPurpose((p) => ({
        ...p,
        detected_data_categories: p.detected_data_categories.filter(
          (c) => !catSet.has(c),
        ),
      }));
      message.success(
        categories.length === 1
          ? `Marked "${categories[0]}" as misclassified`
          : `Marked ${categories.length} categories as misclassified`,
      );
    },
    [message],
  );

  const handleRemoveDatasets = useCallback(
    (datasetKeys: string[]) => {
      if (datasetKeys.length === 0) return;
      const keySet = new Set(datasetKeys);
      setDatasets((ds) =>
        ds.filter((d) => !keySet.has(d.dataset_fides_key)),
      );
      message.success(
        datasetKeys.length === 1
          ? "Dataset removed from purpose"
          : `${datasetKeys.length} datasets removed from purpose`,
      );
    },
    [message],
  );

  return (
    <Flex vertical gap="large">
      <PurposeGovernanceAlert
        purpose={purpose}
        datasets={datasets}
        onAcceptCategories={handleAcceptCategories}
      />
      <AssignedSystemsSection
        systems={systems}
        datasets={datasets}
        definedCategories={purpose.data_categories}
        onSystemsChange={setSystems}
      />
      <AssignedDatasetsSection
        datasets={datasets}
        definedCategories={purpose.data_categories}
        onDatasetsChange={setDatasets}
        onAcceptCategories={handleAcceptCategories}
        onMarkMisclassified={handleMarkMisclassified}
        onRemoveDatasets={handleRemoveDatasets}
      />
    </Flex>
  );
};

export default PurposeDashboard;
