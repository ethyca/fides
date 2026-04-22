import { Flex } from "fidesui";

import AssignedDatasetsSection from "./AssignedDatasetsSection";
import AssignedSystemsSection from "./AssignedSystemsSection";
import PurposeGovernanceAlert from "./PurposeGovernanceAlert";

interface PurposeDashboardProps {
  fidesKey: string;
}

const PurposeDashboard = ({ fidesKey }: PurposeDashboardProps) => (
  <Flex vertical gap="large">
    <PurposeGovernanceAlert fidesKey={fidesKey} />
    <AssignedSystemsSection fidesKey={fidesKey} />
    <AssignedDatasetsSection fidesKey={fidesKey} />
  </Flex>
);

export default PurposeDashboard;
