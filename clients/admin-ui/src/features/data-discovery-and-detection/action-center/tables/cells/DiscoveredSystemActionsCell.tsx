import { AntFlex as Flex } from "fidesui";

import { MonitorAssetsBySystem } from "../../types";

interface DiscoveredSystemActionsCellProps {
  system: MonitorAssetsBySystem;
}

export const DiscoveredSystemActionsCell = ({
  system,
}: DiscoveredSystemActionsCellProps) => {
  console.log(system);
  return <Flex> </Flex>;
};
