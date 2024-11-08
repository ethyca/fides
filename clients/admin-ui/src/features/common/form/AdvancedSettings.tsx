import { ChevronDownIcon, Collapse, Flex, Text, useDisclosure } from "fidesui";
import { ReactNode } from "react";

const AdvancedSettings = ({ children }: { children: ReactNode }) => {
  const { isOpen, onToggle } = useDisclosure();
  return (
    <Flex
      p={4}
      gap={6}
      direction="column"
      border="1px solid"
      borderColor="gray.200"
    >
      <Flex justifyContent="space-between" cursor="pointer" onClick={onToggle}>
        <Text fontSize="xs">Advanced settings</Text>
        <ChevronDownIcon className={isOpen ? "rotate-180" : undefined} />
      </Flex>
      <Collapse in={isOpen}>
        <Flex direction="column" gap={4}>
          {children}
        </Flex>
      </Collapse>
    </Flex>
  );
};

export default AdvancedSettings;
