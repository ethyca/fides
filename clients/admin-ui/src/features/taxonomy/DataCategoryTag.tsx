import { Tag, TagCloseButton, TagLabel } from "@fidesui/react";

import { FidesKey } from "~/features/common/fides-types";

interface Props {
  name: FidesKey;
  onClose?: () => void;
}
const DataCategoryTag = ({ name, onClose }: Props) => {
  if (!onClose) {
    return (
      <Tag backgroundColor="primary.400" color="white" size="sm">
        {name}
      </Tag>
    );
  }
  return (
    <Tag
      backgroundColor="primary.400"
      color="white"
      display="flex"
      justifyContent="space-between"
      width="fit-content"
    >
      <TagLabel>{name}</TagLabel>
      <TagCloseButton onClick={onClose} color="white" />
    </Tag>
  );
};

export default DataCategoryTag;
