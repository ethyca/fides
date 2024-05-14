import { HStack } from "fidesui";
import { FC } from "react";

export const TableActionBar: FC = ({ children }) => (
  <HStack
    justifyContent="space-between"
    alignItems="center"
    p={2}
    borderWidth="1px"
    borderBottomWidth="0px"
    borderColor="gray.200"
  >
    {children}
  </HStack>
);
