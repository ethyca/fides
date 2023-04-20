import { PRIVACY_REQUESTS_ROUTE } from "@fidesui/components";
import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  Button,
  Flex,
  Heading,
  Spinner,
  Text,
} from "@fidesui/react";
import Restrict, { useHasPermission } from "common/Restrict";
import EmptyTableState from "common/table/EmptyTableState";
import NextLink from "next/link";
import React, { useMemo } from "react";
import { CellProps, Column } from "react-table";

import { useAppSelector } from "~/app/hooks";
import Layout from "~/features/common/Layout";
import {
  PRIVACY_NOTICES_ROUTE,
  SYSTEM_ROUTE,
} from "~/features/common/nav/v2/routes";
import {
  DateCell,
  EnableCell,
  FidesTable,
  FidesTableFooter,
  MechanismCell,
  MultiTagCell,
  TitleCell,
  WrappedCell,
} from "~/features/common/table";
import {
  selectAllPrivacyNotices,
  selectPage,
  selectPageSize,
  useGetAllPrivacyNoticesQuery,
  usePatchPrivacyNoticesMutation,
} from "~/features/privacy-notices/privacy-notices.slice";
import { PrivacyNoticeResponse, ScopeRegistryEnum } from "~/types/api";

const EnablePrivacyNoticeCell = (
  cellProps: CellProps<PrivacyNoticeResponse, boolean>
) => {
  const [patchNoticeMutationTrigger] = usePatchPrivacyNoticesMutation();

  const { row } = cellProps;
  const onToggle = async (toggle: boolean) => {
    await patchNoticeMutationTrigger([
      {
        id: row.original.id,
        disabled: !toggle,
      },
    ]);
  };
  return (
    <EnableCell<PrivacyNoticeResponse>
      {...cellProps}
      onToggle={onToggle}
      title="Disable privacy notice"
      message="Are you sure you want to disable this privacy notice? Disabling this
            notice means your users will no longer see this explanation about
            your data uses which is necessary to ensure compliance."
    />
  );
};

const PrivacyNoticesPage = () => {
  // Subscribe to get all privacy notices
  const page = useAppSelector(selectPage);
  const pageSize = useAppSelector(selectPageSize);
  const { isLoading } = useGetAllPrivacyNoticesQuery({ page, size: pageSize });

  const privacyNotices = useAppSelector(selectAllPrivacyNotices);
  // Permissions
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.PRIVACY_NOTICE_UPDATE,
  ]);

  const columns: Column<PrivacyNoticeResponse>[] = useMemo(
    () => [
      {
        Header: "Title",
        accessor: "name",
        Cell: TitleCell,
      },
      {
        Header: "Description",
        accessor: "description",
        Cell: WrappedCell,
      },
      {
        Header: "Mechanism",
        accessor: "consent_mechanism",
        Cell: MechanismCell,
      },
      { Header: "Locations", accessor: "regions", Cell: MultiTagCell },
      { Header: "Created", accessor: "created_at", Cell: DateCell },
      { Header: "Last update", accessor: "updated_at", Cell: DateCell },
      {
        Header: "Enable",
        accessor: "disabled",
        disabled: !userCanUpdate,
        Cell: EnablePrivacyNoticeCell,
      },
    ],
    [userCanUpdate]
  );

  if (isLoading) {
    return (
      <Flex height="100%" justifyContent="center" alignItems="center">
        <Spinner />
      </Flex>
    );
  }

  if (privacyNotices.length === 0) {
    return (
      <EmptyTableState
        title="To start configuring consent, please first add data uses"
        description="It looks like you have not yet added any data uses to the system. Fides
        relies on how you use data in your organization to provide intelligent
        recommendations and pre-built templates for privacy notices you may need
        to display to your users. To get started with privacy notices, first add
        your data uses to systems on your data map."
        buttonHref={SYSTEM_ROUTE}
        buttonText="Set up data uses"
      />
    );
  }

  return (
    <Layout title="Privacy notices">
      <Box mb={4}>
        <Heading
          fontSize="2xl"
          fontWeight="semibold"
          mb={2}
          data-testid="header"
        >
          Manage privacy notices
        </Heading>
        <Box>
          <Breadcrumb
            fontWeight="medium"
            fontSize="sm"
            color="gray.600"
            data-testid="breadcrumbs"
          >
            <BreadcrumbItem>
              <NextLink href={PRIVACY_REQUESTS_ROUTE}>
                Privacy requests
              </NextLink>
            </BreadcrumbItem>
            {/* TODO: Add Consent breadcrumb once the page exists */}
            <BreadcrumbItem color="complimentary.500">
              <NextLink href={PRIVACY_NOTICES_ROUTE}>Privacy notices</NextLink>
            </BreadcrumbItem>
          </Breadcrumb>
        </Box>
      </Box>
      <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "50%" }}>
        Manage the privacy notices and mechanisms that are displayed to your
        users based on their location, what information you collect about them,
        and how you use that data.
      </Text>
      <Box data-testid="privacy-notices-page">
        <FidesTable<PrivacyNoticeResponse>
          columns={columns}
          data={privacyNotices}
          userCanUpdate={userCanUpdate}
          redirectRoute={PRIVACY_NOTICES_ROUTE}
          footer={
            <FidesTableFooter totalColumns={columns.length}>
              <Restrict scopes={[ScopeRegistryEnum.PRIVACY_NOTICE_CREATE]}>
                <NextLink href={`${PRIVACY_NOTICES_ROUTE}/new`}>
                  <Button
                    size="xs"
                    colorScheme="primary"
                    data-testid="add-privacy-notice-btn"
                  >
                    Add a privacy notice +
                  </Button>
                </NextLink>
              </Restrict>
            </FidesTableFooter>
          }
        />
      </Box>
    </Layout>
  );
};

export default PrivacyNoticesPage;
