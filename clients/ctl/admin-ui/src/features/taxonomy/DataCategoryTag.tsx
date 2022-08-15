import { Tag, TagCloseButton, TagLabel } from "@fidesui/react";

interface Props {
  name: string;
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
      data-testid={`data-category-${name}`}
    >
      <TagLabel>{name}</TagLabel>
      <TagCloseButton onClick={onClose} color="white" />
    </Tag>
  );
};

export default DataCategoryTag;
