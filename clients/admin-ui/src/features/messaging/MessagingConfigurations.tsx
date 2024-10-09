import { AntButton as Button, Flex, Heading, HStack, Text } from "fidesui";

import Layout from "~/features/common/Layout";
import { ScopeRegistryEnum } from "~/types/api";

import { MESSAGING_CONFIGURATION_ROUTE } from "../common/nav/v2/routes";
import { useHasPermission } from "../common/Restrict";
import { TableActionBar } from "../common/table/v2";

export const MessagingConfigurations = () => {
  // Permissions
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE,
  ]);

  return (
    <Layout title="Messaging Configurations">
      <Heading mb={5} fontSize="2xl" fontWeight="semibold">
        Manage messaging configurations
      </Heading>
      <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "50%" }}>
        Fides requires a messaging provider for sending processing notices to
        privacy request subjects, and allows for Subject Identity Verification
        in privacy requests. Please follow the{" "}
        <Text as="span" color="complimentary.500">
          documentation
        </Text>{" "}
        to setup a messaging service that Fides supports. Ensure you have
        completed the setup for the preferred messaging provider and have the
        details handy prior to the following steps.
      </Text>
      <Flex flex={1} direction="column" overflow="auto">
        {userCanUpdate && (
          <TableActionBar>
            <HStack alignItems="center" spacing={4} marginLeft="auto">
              <Button
                href={`${MESSAGING_CONFIGURATION_ROUTE}/new`}
                role="link"
                size="small"
                type="primary"
                data-testid="add-privacy-notice-btn"
              >
                Add a messaging config +
              </Button>
            </HStack>
          </TableActionBar>
        )}
      </Flex>
    </Layout>
  );
};
