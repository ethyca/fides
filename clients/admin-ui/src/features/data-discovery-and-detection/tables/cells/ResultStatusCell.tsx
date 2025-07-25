import { AntSpace as Space, AntTooltip as Tooltip, Text } from "fidesui";

import { STATUS_INDICATOR_MAP } from "~/features/data-discovery-and-detection/statusIndicators";
import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import findResourceChangeType from "~/features/data-discovery-and-detection/utils/findResourceChangeType";
import getResourceName from "~/features/data-discovery-and-detection/utils/getResourceName";
import resourceHasChildren from "~/features/data-discovery-and-detection/utils/resourceHasChildren";
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
    <Space className="h-full">
      <Tooltip title={changeType}>
        {/* icon has to be wrapped in a span for the tooltip to work */}
        <span>{STATUS_INDICATOR_MAP[changeType]}</span>
      </Tooltip>
      <Text
        fontSize="xs"
        lineHeight={4}
        fontWeight={resourceHasChildren(result) ? "semibold" : "normal"}
        overflow="hidden"
        textOverflow="ellipsis"
      >
        {getResourceName(result)}
      </Text>
    </Space>
  );
};

export default ResultStatusCell;
