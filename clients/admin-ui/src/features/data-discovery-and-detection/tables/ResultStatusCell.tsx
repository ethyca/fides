import { Flex, Text } from "@fidesui/react";

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
      return <RightUpArrowIcon color="green.400" boxSize={2} mr={2} />;
    case ResourceChangeType.REMOVAL:
      return <RightDownArrowIcon color="red.400" boxSize={2} mr={2} />;
    case ResourceChangeType.CLASSIFICATION:
      return <TagIcon color="orange.400" boxSize={3} mr={2} />;
    case ResourceChangeType.CHANGE:
      return <CircleIcon color="blue.400" boxSize={2} mr={2} />;
    default:
      return null;
  }
};

const ResultStatusCell = ({ result }: { result: StagedResource }) => (
  <Flex alignItems="center" height="100%">
    {getResourceChangeIcon(findResourceChangeType(result))}
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

export default ResultStatusCell;
