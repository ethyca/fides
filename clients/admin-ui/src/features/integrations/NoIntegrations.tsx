import { AntButton as Button, Flex, Text } from "fidesui";

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
    <Button type="primary" onClick={onOpenAddModal} className="mt-4">
      Add integration
    </Button>
  </Flex>
);

export default NoIntegrations;
