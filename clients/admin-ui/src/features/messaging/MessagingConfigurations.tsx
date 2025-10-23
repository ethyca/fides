/* eslint-disable react/no-unstable-nested-components */
import {
  AntButton as Button,
  AntSpace as Space,
  AntTable as Table,
  Flex,
  Icons,
  Text,
  VStack,
} from "fidesui";
import { useRouter } from "next/router";

import { MESSAGING_PROVIDERS_NEW_ROUTE } from "~/features/common/nav/routes";

import { TableSkeletonLoader } from "../common/table/v2";
import { useMessagingConfigurationsTable } from "./hooks/useMessagingConfigurationsTable";

const EmptyTableNotice = () => {
  return (
    <VStack
      mt={6}
      p={10}
      spacing={4}
      borderRadius="base"
      maxW="70%"
      data-testid="no-results-notice"
      alignSelf="center"
      margin="auto"
    >
      <VStack>
        <Text fontSize="md" fontWeight="600">
          No messaging providers found.
        </Text>
        <Text fontSize="sm">
          Click &quot;Add a messaging provider&quot; to add your first messaging
          provider to Fides.
        </Text>
      </VStack>
    </VStack>
  );
};

export const MessagingConfigurations = () => {
  const {
    // Table state and data
    columns,

    // Ant Design table integration
    tableProps,

    // Business state
    userCanUpdate,
    isLoading,

    // Modal components
    deleteModal,
  } = useMessagingConfigurationsTable();

  const router = useRouter();

  return (
    <>
      <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "70%" }}>
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
          <Space
            direction="horizontal"
            style={{
              width: "100%",
              justifyContent: "flex-end",
              marginBottom: 16,
            }}
          >
            <Button
              onClick={() => {
                router.push(MESSAGING_PROVIDERS_NEW_ROUTE);
              }}
              role="link"
              type="primary"
              icon={<Icons.Add />}
              iconPosition="end"
              data-testid="add-messaging-provider-btn"
            >
              Add a messaging provider
            </Button>
          </Space>
        )}
        {isLoading ? (
          <TableSkeletonLoader rowHeight={36} numRows={5} />
        ) : (
          <Table
            {...tableProps}
            columns={columns}
            locale={{
              emptyText: <EmptyTableNotice />,
            }}
          />
        )}
      </Flex>

      {deleteModal}
    </>
  );
};
