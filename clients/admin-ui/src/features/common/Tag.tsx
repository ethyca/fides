import { Tag as BaseTag } from "@fidesui/react";

const Tag = ({children}) =>
    <BaseTag
      borderRadius="2px"
      padding="4px 8px"
      bg="gray.100"
      color="gray.600"
      marginRight="4px">
        {children}
    </BaseTag>

export default Tag
