import { Tag, TagCloseButton, TagLabel, TagProps } from "@fidesui/react";

interface Props {
  name: string;
  onClose?: () => void;
}
const TaxonomyEntityTag = ({ name, onClose, ...other }: Props & TagProps) => {
  const tagProps = {
    backgroundColor: "primary.400",
    color: "white",
    "data-testid": `taxonomy-entity-${name}`,
    width: "fit-content",
    size: "sm",
    ...other,
  };

  if (!onClose) {
    return <Tag {...tagProps}>{name}</Tag>;
  }
  return (
    <Tag display="flex" justifyContent="space-between" {...tagProps}>
      <TagLabel>{name}</TagLabel>
      <TagCloseButton onClick={onClose} color="white" />
    </Tag>
  );
};

export default TaxonomyEntityTag;
