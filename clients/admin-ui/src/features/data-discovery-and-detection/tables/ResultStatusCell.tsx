import { Flex, Text, Tooltip } from "fidesui";

import { STATUS_INDICATOR_MAP } from "~/features/data-discovery-and-detection/statusIndicators";
import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import findResourceChangeType from "~/features/data-discovery-and-detection/utils/findResourceChangeType";
import { StagedResource } from "~/types/api";

const ResultStatusCell = ({
  result,
  changeTypeOverride,
}: {
  result: StagedResource;
  changeTypeOverride?: ResourceChangeType;
}) => {
  const changeType = changeTypeOverride ?? findResourceChangeType(result);
  return (
    <Flex alignItems="center" height="100%">
      <Tooltip label={changeType}>
        {/* icon has to be wrapped in a span for the tooltip to work */}
        <span>{STATUS_INDICATOR_MAP[changeType]}</span>
      </Tooltip>
      <Text
        fontSize="xs"
        lineHeight={4}
        fontWeight="normal"
        overflow="hidden"
        textOverflow="ellipsis"
      >
        {result.name}
      </Text>
    </Flex>
  );
};

export default ResultStatusCell;
