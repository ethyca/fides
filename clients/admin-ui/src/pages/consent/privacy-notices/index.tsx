import { PRIVACY_REQUESTS_ROUTE } from "@fidesui/components";
import { Box, Breadcrumb, BreadcrumbItem, Heading, Text } from "@fidesui/react";
import NextLink from "next/link";

import Layout from "~/features/common/Layout";
import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/v2/routes";
import { useRouter } from "next/router";
import { useAppSelector } from "~/app/hooks";
import {
  selectAllPrivacyNotices,
  selectPage,
  selectPageSize,
  useGetAllPrivacyNoticesQuery, usePatchPrivacyNoticesMutation
} from "~/features/privacy-notices/privacy-notices.slice";
import { useHasPermission } from "common/Restrict";
import { PrivacyNoticeResponse, ScopeRegistryEnum } from "~/types/api";
import { Column } from "react-table";
import { useMemo } from "react";
import {
  DateCell,
  EnableCell,
  MechanismCell,
  MultiTagCell,
  TitleCell,
  WrappedCell,
  FidesTable,
} from "~/features/common/table";

const PrivacyNoticesPage = () => {
  // Subscribe to get all privacy notices
  const page = useAppSelector(selectPage);
  const pageSize = useAppSelector(selectPageSize);
  useGetAllPrivacyNoticesQuery({ page, size: pageSize });

  const privacyNotices = useAppSelector(selectAllPrivacyNotices);
  const [patchNoticeMutationTrigger] = usePatchPrivacyNoticesMutation();
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
        Cell: EnableCell,
        onToggle: patchNoticeMutationTrigger
      },
    ],
    [userCanUpdate]
  );
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
        <FidesTable
          columns={columns}
          data={privacyNotices}
          userCanUpdate={userCanUpdate}
          redirectRoute={PRIVACY_NOTICES_ROUTE}
          createScope={ScopeRegistryEnum.PRIVACY_NOTICE_CREATE}
          tableType="privacy notice"
        />
      </Box>
    </Layout>
  );
};

export default PrivacyNoticesPage;
