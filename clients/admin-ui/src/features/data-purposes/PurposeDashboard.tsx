import { Flex } from "fidesui";

import AssignedDatasetsSection from "./AssignedDatasetsSection";
import AssignedSystemsSection from "./AssignedSystemsSection";
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
  systems,
  datasets,
}: PurposeDashboardProps) => {
  return (
    <Flex vertical gap="large">
      <AssignedSystemsSection systems={systems} />
      <AssignedDatasetsSection datasets={datasets} />
    </Flex>
  );
};

export default PurposeDashboard;
