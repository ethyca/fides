import { Flex } from "fidesui";

import AssignedDatasetsSection from "./AssignedDatasetsSection";
import AssignedSystemsSection from "./AssignedSystemsSection";
import CoverageSection from "./CoverageSection";
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
}: PurposeDashboardProps) => (
  <Flex vertical gap="large">
    <CoverageSection
      purpose={purpose}
      coverage={coverage}
      systemCount={systems.length}
      datasetCount={datasets.length}
    />
    <AssignedSystemsSection systems={systems} />
    <AssignedDatasetsSection datasets={datasets} />
  </Flex>
);

export default PurposeDashboard;
