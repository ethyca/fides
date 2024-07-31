import { Flex, Text, Tooltip } from "fidesui";

import { CircleIcon } from "~/features/common/Icon/CircleIcon";
import { RightDownArrowIcon } from "~/features/common/Icon/RightDownArrowIcon";
import { RightUpArrowIcon } from "~/features/common/Icon/RightUpArrowIcon";
import { TagIcon } from "~/features/common/Icon/TagIcon";
import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import findResourceChangeType from "~/features/data-discovery-and-detection/utils/findResourceChangeType";
import { StagedResource } from "~/types/api";

export const ResourceChangeTypeIcons = [
  {
    type: ResourceChangeType.CHANGE,
    icon: CircleIcon,
    color: "blue.400",
    label: "Change detected",
  },
  {
    type: ResourceChangeType.ADDITION,
    icon: RightUpArrowIcon,
    color: "green.400",
    label: "Addition detected",
  },
  {
    type: ResourceChangeType.CLASSIFICATION,
    icon: TagIcon,
    color: "orange.400",
    label: "Classification detected",
  },
  {
    type: ResourceChangeType.REMOVAL,
    icon: RightDownArrowIcon,
    color: "red.400",
    label: "Removal detected",
  },
];

const getResourceChangeIcon = (changeType: ResourceChangeType) => {
  const iconConfig = ResourceChangeTypeIcons.find(
    (icon) => icon.type === changeType
  );
  if (iconConfig) {
    const { icon: Icon, color } = iconConfig;
    return (
      <Tooltip label={changeType}>
        <Icon
          color={color}
          boxSize={changeType === ResourceChangeType.CLASSIFICATION ? 3 : 2}
          mr={2}
          data-testid={`${changeType.toLowerCase()}-icon`}
        />
      </Tooltip>
    );
  }
  return null;
};

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
      {getResourceChangeIcon(changeType)}
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
