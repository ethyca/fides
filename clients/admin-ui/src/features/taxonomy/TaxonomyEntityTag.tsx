import { Tag, TagCloseButton, TagLabel, TagProps } from "@fidesui/react";

interface Props {
  name: string;
  onClose?: () => void;
}
const TaxonomyEntityTag = ({ name, onClose, ...other }: Props & TagProps) => {
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
      {...other}
    >
      <TagLabel>{name}</TagLabel>
      <TagCloseButton onClick={onClose} color="white" />
    </Tag>
  );
};

export default TaxonomyEntityTag;
