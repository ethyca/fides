import { AntFlex as Flex } from "fidesui";

import { StagedResourceAPIResponse } from "~/types/api";

interface DiscoveredAssetActionsCellProps {
  asset: StagedResourceAPIResponse;
}

export const DiscoveredAssetActionsCell = ({
  asset,
}: DiscoveredAssetActionsCellProps) => {
  console.log(asset);
  return <Flex> </Flex>;
};
