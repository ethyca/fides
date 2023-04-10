import { Box, Button, HStack, Text, WarningTwoIcon } from "@fidesui/react";
import NextLink from "next/link";

import { SYSTEM_ROUTE } from "~/features/common/nav/v2/routes";

const EmptyState = () => (
  <HStack
    backgroundColor="gray.50"
    border="1px solid"
    borderColor="blue.400"
    borderRadius="md"
    justifyContent="space-between"
    py={4}
    px={6}
    data-testid="empty-state"
  >
    <WarningTwoIcon alignSelf="start" color="blue.400" mt={0.5} />
    <Box>
      <Text fontWeight="bold" fontSize="sm" mb={1}>
        To start configuring consent, please first add data uses
      </Text>

      <Text fontSize="sm" color="gray.600" lineHeight="5">
        It looks like you have not yet added any data uses to the system. Fides
        relies on how you use data in your organization to provide intelligent
        recommendations and pre-built templates for privacy notices you may need
        to display to your users. To get started with privacy notices, first add
        your data uses to systems on your data map. To learn more about data
        uses and consent, read the Consent Guide now.
      </Text>
    </Box>
    <Button size="sm" variant="outline" fontWeight="semibold" minWidth="auto">
      <NextLink href={SYSTEM_ROUTE}>Set up data uses</NextLink>
    </Button>
  </HStack>
);

export default EmptyState;
