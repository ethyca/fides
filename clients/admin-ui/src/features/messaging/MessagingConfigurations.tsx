/* eslint-disable react/no-unstable-nested-components */
import {
  ColumnDef,
  createColumnHelper,
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { isErrorResult } from "common/helpers";
import { useAPIHelper } from "common/hooks";
import {
  AntButton as Button,
  Badge,
  BadgeProps,
  Flex,
  Heading,
  HStack,
  Text,
  useToast,
  VStack,
} from "fidesui";
import { useEffect, useMemo, useState } from "react";

import Layout from "~/features/common/Layout";
import { usePatchConfigurationSettingsMutation } from "~/features/privacy-requests";
import {
  MessagingConfigResponse,
  MessagingServiceType,
  ScopeRegistryEnum,
} from "~/types/api";

import { MESSAGING_CONFIGURATION_ROUTE } from "../common/nav/v2/routes";
import { useHasPermission } from "../common/Restrict";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  TableActionBar,
} from "../common/table/v2";
import { RelativeTimestampCell } from "../common/table/v2/cells";
import { successToastParams } from "../common/toast";
import MailgunIcon from "./MailgunIcon";
import {
  useGetActiveMessagingProviderQuery,
  useGetMessagingConfigurationsQuery,
} from "./messaging.slice";
import { TestMessagingProviderModal } from "./TestMessagingProviderModal";
import TwilioIcon from "./TwilioIcon";

const columnHelper = createColumnHelper<MessagingConfigResponse>();

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
          No messaging configs found.
        </Text>
        <Text fontSize="sm">
          Click &quot;Add a messaging config&quot; to add your first messaing
          config to Fides.
        </Text>
      </VStack>
    </VStack>
  );
};

const ResultStatusBadge = ({ children, ...props }: BadgeProps) => {
  return (
    <Badge fontSize="xs" fontWeight="normal" textTransform="none" {...props}>
      {children}
    </Badge>
  );
};

export const MessagingConfigurations = () => {
  const toast = useToast();
  const { handleError } = useAPIHelper();
  const [messagingValue, setMessagingValue] = useState("");
  const [saveActiveConfiguration] = usePatchConfigurationSettingsMutation();
  const { data: activeMessagingProvider } =
    useGetActiveMessagingProviderQuery();

  // Permissions
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE,
  ]);

  const [selectedServiceType, setSelectedServiceType] =
    useState<MessagingConfigResponse["service_type"]>();

  const { data } = useGetMessagingConfigurationsQuery();

  useEffect(() => {
    if (activeMessagingProvider) {
      setMessagingValue(activeMessagingProvider?.service_type);
    }
  }, [activeMessagingProvider]);

  const setActiveServiceType = async (serviceType: MessagingServiceType) => {
    const result = await saveActiveConfiguration({
      notifications: {
        notification_service_type: serviceType,
      },
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      setMessagingValue(serviceType);
      toast(successToastParams("Updated active messaging config"));
    }
  };

  const messagingConfigColumns: ColumnDef<MessagingConfigResponse, any>[] =
    useMemo(
      () => [
        columnHelper.accessor((row) => row.name, {
          id: "name",
          cell: (props) => (
            // eslint-disable-next-line no-nested-ternary
            <HStack>
              {props.row.original.service_type === "mailgun" ? (
                <MailgunIcon />
              ) : (
                <TwilioIcon />
              )}
              <DefaultCell value={props.getValue()} />
              {props.row.original.service_type === messagingValue && (
                <ResultStatusBadge colorScheme="green">
                  Active
                </ResultStatusBadge>
              )}
            </HStack>
          ),
          header: (props) => (
            <DefaultHeaderCell value="Service type" {...props} />
          ),
        }),
        columnHelper.accessor((row) => row.last_test_succeeded, {
          id: "last_test_succeeded",
          cell: (props) =>
            // eslint-disable-next-line no-nested-ternary
            props.getValue() ? (
              <ResultStatusBadge colorScheme="green">Success</ResultStatusBadge>
            ) : (
              props.row.original.last_test_timestamp && (
                <ResultStatusBadge colorScheme="red">Error</ResultStatusBadge>
              )
            ),
          header: (props) => (
            <DefaultHeaderCell value="Last test status" {...props} />
          ),
        }),
        columnHelper.accessor((row) => row.last_test_timestamp, {
          id: "last_test_timestamp",
          cell: (props) => <RelativeTimestampCell time={props.getValue()} />,
          header: (props) => (
            <DefaultHeaderCell value="Last tested" {...props} />
          ),
        }),
        columnHelper.display({
          id: "actions",
          cell: (props) => (
            <HStack>
              <Button
                onClick={() =>
                  setSelectedServiceType(props.row.original.service_type)
                }
                size="small"
              >
                Test config
              </Button>
              <Button
                onClick={() =>
                  setActiveServiceType(props.row.original.service_type)
                }
                disabled={props.row.original.service_type === messagingValue}
                size="small"
              >
                Set Active
              </Button>
            </HStack>
          ),
          header: "Actions",
        }),
      ],
      // eslint-disable-next-line react-hooks/exhaustive-deps
      [activeMessagingProvider, messagingValue],
    );

  const tableInstance = useReactTable<MessagingConfigResponse>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    columns: messagingConfigColumns,
    manualPagination: true,
    data: data?.items ?? [],
    state: {
      expanded: true,
    },
    columnResizeMode: "onChange",
  });

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
        <FidesTableV2
          tableInstance={tableInstance}
          emptyTableNotice={<EmptyTableNotice />}
        />
      </Flex>
      {!!selectedServiceType && (
        <TestMessagingProviderModal
          serviceType={selectedServiceType}
          isOpen={!!selectedServiceType}
          onClose={() => setSelectedServiceType(undefined)}
        />
      )}
    </Layout>
  );
};
