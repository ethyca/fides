import { HStack, StackProps } from "fidesui";

export const TableActionBar = ({ children, ...props }: StackProps) => (
  <HStack
    justifyContent="space-between"
    alignItems="center"
    p={2}
    borderWidth="1px"
    borderBottomWidth="0px"
    borderColor="gray.200"
    {...props}
  >
    {children}
  </HStack>
);
