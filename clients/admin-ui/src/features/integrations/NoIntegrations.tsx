import { Button, Flex, Text } from "fidesui";

const NoIntegrations = ({ onOpenAddModal }: { onOpenAddModal: () => void }) => (
  <Flex direction="column" alignItems="center">
    <Text color="gray.700" fontWeight="semibold" fontSize="xl">
      No integrations
    </Text>
    <Text color="gray.700" marginTop="8px">
      You have not configured any integrations
    </Text>
    <Text color="gray.700">
      Click &quot;Add integration&quot; to connect and configure systems now.
    </Text>
    <Button variant="primary" marginTop="16px" onClick={onOpenAddModal}>
      Add integration
    </Button>
  </Flex>
);

export default NoIntegrations;
