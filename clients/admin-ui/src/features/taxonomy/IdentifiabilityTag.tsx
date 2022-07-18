import { Tag } from "@fidesui/react";

import { DATA_QUALIFIERS } from "~/features/dataset/constants";

interface Props {
  dataQualifierName: string;
}
const IdentifiabilityTag = ({ dataQualifierName }: Props) => {
  const qualifiers = DATA_QUALIFIERS.filter(
    (dq) => dq.key === dataQualifierName
  );
  if (qualifiers.length === 0) {
    // not found in our default taxonomy, render as-is for now
    return <Tag>{dataQualifierName}</Tag>;
  }
  const qualifier = qualifiers[0];
  const { styles, label, key } = qualifier;

  return (
    <Tag data-testid={`identifiability-tag-${key}`} {...styles}>
      {label}
    </Tag>
  );
};

export default IdentifiabilityTag;
