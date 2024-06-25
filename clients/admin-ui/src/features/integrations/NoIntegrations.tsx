import { Button, Flex, Text } from "fidesui";

const NoIntegrations = ({
  isFiltered,
  onOpenAddModal,
}: {
  isFiltered?: boolean;
  onOpenAddModal: () => void;
}) => (
  <Flex direction="column" alignItems="center" data-testid="empty-state">
    <Text color="gray.700" fontWeight="semibold" fontSize="md">
      No integrations
    </Text>
    <Text color="gray.700" fontSize="sm" marginTop="8px">
      {isFiltered
        ? "No integrations match your filters"
        : "You have not configured any integrations"}
    </Text>
    <Text color="gray.700" fontSize="sm">
      Click &quot;Add integration&quot; to connect and configure systems now.
    </Text>
    <Button
      variant="primary"
      size="sm"
      marginTop="16px"
      onClick={onOpenAddModal}
    >
      Add integration
    </Button>
  </Flex>
);

export default NoIntegrations;
