import { Flex, Text, Tooltip } from "@fidesui/react";

import { CircleIcon } from "~/features/common/Icon/CircleIcon";
import { RightDownArrowIcon } from "~/features/common/Icon/RightDownArrowIcon";
import { RightUpArrowIcon } from "~/features/common/Icon/RightUpArrowIcon";
import { TagIcon } from "~/features/common/Icon/TagIcon";
import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import findResourceChangeType from "~/features/data-discovery-and-detection/utils/findResourceChangeType";
import { StagedResource } from "~/types/api";

const getResourceChangeIcon = (changeType: ResourceChangeType) => {
  switch (changeType) {
    case ResourceChangeType.ADDITION:
      return (
        <Tooltip label="Addition">
          <RightUpArrowIcon
            color="green.400"
            boxSize={2}
            mr={2}
            data-testid="add-icon"
          />
        </Tooltip>
      );
    case ResourceChangeType.REMOVAL:
      return (
        <Tooltip label="Removal">
          <RightDownArrowIcon
            color="red.400"
            boxSize={2}
            mr={2}
            data-testid="remove-icon"
          />
        </Tooltip>
      );
    case ResourceChangeType.CLASSIFICATION:
      return (
        <Tooltip label="Classification">
          <TagIcon
            color="orange.400"
            boxSize={3}
            mr={2}
            data-testid="classify-icon"
          />
        </Tooltip>
      );
    case ResourceChangeType.CHANGE:
      return (
        <Tooltip label="Update">
          <CircleIcon
            color="blue.400"
            boxSize={2}
            mr={2}
            data-testid="change-icon"
          />
        </Tooltip>
      );
    default:
      return null;
  }
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
