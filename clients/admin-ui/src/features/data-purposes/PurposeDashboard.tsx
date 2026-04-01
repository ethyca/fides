import { Flex } from "fidesui";

import { ProgressCard } from "~/features/data-discovery-and-detection/action-center/ProgressCard/ProgressCard";

import AssignedDatasetsSection from "./AssignedDatasetsSection";
import AssignedSystemsSection from "./AssignedSystemsSection";
import { getCompleteness } from "./purposeUtils";
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
  purpose,
  coverage,
  systems,
  datasets,
}: PurposeDashboardProps) => {
  const completeness = getCompleteness(purpose);
  const assignedSystems = systems.filter((s) => s.assigned);

  return (
    <Flex vertical gap="large">
      <ProgressCard
        title={purpose.name}
        subtitle={purpose.data_use}
        compact
        progress={{
          label: "Completeness",
          percent: completeness,
          numerator: completeness,
          denominator: 100,
        }}
        numericStats={{
          label: "Coverage",
          data: [
            { label: "data consumers", count: assignedSystems.length },
            { label: "datasets", count: datasets.length },
            { label: "tables", count: coverage.tables.assigned },
            { label: "fields", count: coverage.fields.assigned },
          ],
        }}
        percentageStats={{
          label: "Assigned vs total",
          data: [
            {
              label: "systems",
              value: coverage.systems.total > 0
                ? Math.round((coverage.systems.assigned / coverage.systems.total) * 100)
                : 0,
            },
            {
              label: "datasets",
              value: coverage.datasets.total > 0
                ? Math.round((coverage.datasets.assigned / coverage.datasets.total) * 100)
                : 0,
            },
          ],
        }}
        lastUpdated={purpose.updated_at}
      />
      <AssignedSystemsSection systems={systems} />
      <AssignedDatasetsSection datasets={datasets} />
    </Flex>
  );
};

export default PurposeDashboard;
