import { Flex } from "fidesui";

export const ConfigColumnLayout = ({
  buttonPanel,
  children,
}: {
  buttonPanel: React.ReactNode;
  children: React.ReactNode;
}) => (
  <Flex vertical className="min-h-full w-full">
    <Flex vertical className="h-full overflow-y-auto px-4">
      {children}
    </Flex>
    {buttonPanel}
  </Flex>
);
