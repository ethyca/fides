import { Tag as BaseTag } from "fidesui";
import { ReactNode } from "react";

const Tag = ({ children }: { children: ReactNode }) => (
  <BaseTag
    borderRadius="2px"
    padding="4px 8px"
    bg="neutral.100"
    color="neutral.600"
    marginRight="4px"
    height="24px"
    fontWeight={400}
    fontSize="xs"
  >
    {children}
  </BaseTag>
);

export default Tag;
