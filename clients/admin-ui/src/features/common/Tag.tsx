import { Tag as BaseTag } from "@fidesui/react";

const Tag = (props) =>
    <BaseTag
      borderRadius="2px"
      padding="4px 8px"
      bg="gray.100"
      color="gray.600"
      marginRight="4px">
        {props.children}
    </BaseTag>

export default Tag
