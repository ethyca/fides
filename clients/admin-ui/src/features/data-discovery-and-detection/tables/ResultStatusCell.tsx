import { Flex, Text } from "@fidesui/react";

import { CircleIcon } from "~/features/common/Icon/CircleIcon";
import { RightDownArrowIcon } from "~/features/common/Icon/RightDownArrowIcon";
import { RightUpArrowIcon } from "~/features/common/Icon/RightUpArrowIcon";
import { TagIcon } from "~/features/common/Icon/TagIcon";
import { DiffStatus, StagedResource } from "~/types/api";

const getResourceChangeIcon = (resource: StagedResource) => {
  if (resource.diff_status === DiffStatus.ADDITION) {
    return <RightUpArrowIcon color="green.400" boxSize={2} mr={2} />;
  }
  if (resource.diff_status === DiffStatus.REMOVAL) {
    return <RightDownArrowIcon color="red.400" boxSize={2} mr={2} />;
  }
  if (
    resource.diff_status === DiffStatus.CLASSIFICATION_ADDITION ||
    resource.diff_status === DiffStatus.CLASSIFICATION_UPDATE
  ) {
    return <TagIcon color="orange.400" boxSize={3} mr={2} />;
  }
  if (
    resource.child_diff_statuses!.addition ||
    resource.child_diff_statuses!.removal
  ) {
    return <CircleIcon color="blue.400" boxSize={2} mr={2} />;
  }
  return null;
};

const ResultStatusCell = ({ result }: { result: StagedResource }) => (
  <Flex alignItems="center" height="100%">
    {getResourceChangeIcon(result)}
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
