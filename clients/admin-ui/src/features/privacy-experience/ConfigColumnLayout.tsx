import { Flex } from "fidesui";

export const ConfigColumnLayout = ({
  buttonPanel,
  children,
}: {
  buttonPanel: React.ReactNode;
  children: React.ReactNode;
}) => (
  <Flex
    vertical
    className="min-h-full w-full"
    style={{ borderRight: "1px solid var(--ant-color-border)" }}
  >
    <Flex vertical className="h-full overflow-y-auto px-4">
      <Flex vertical gap="large" className="w-full pb-6">
        {children}
      </Flex>
    </Flex>
    {buttonPanel}
  </Flex>
);
