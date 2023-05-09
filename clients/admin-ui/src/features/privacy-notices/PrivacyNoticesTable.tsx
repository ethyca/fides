import { Button, Flex, Spinner } from "@fidesui/react";
import { PRIVACY_NOTICES_ROUTE, SYSTEM_ROUTE } from "common/nav/v2/routes";
import Restrict, { useHasPermission } from "common/Restrict";
import {
  DateCell,
  FidesTable,
  FidesTableFooter,
  MultiTagCell,
  TitleCell,
  WrappedCell,
} from "common/table";
import EmptyTableState from "common/table/EmptyTableState";
import NextLink from "next/link";
import { useRouter } from "next/router";
import React, { useMemo } from "react";
import { Column } from "react-table";

import { useAppSelector } from "~/app/hooks";
import {
  EnablePrivacyNoticeCell,
  MechanismCell,
} from "~/features/privacy-notices/cells";
import {
  selectAllPrivacyNotices,
  selectPage,
  selectPageSize,
  useGetAllPrivacyNoticesQuery,
} from "~/features/privacy-notices/privacy-notices.slice";
import { PrivacyNoticeResponse, ScopeRegistryEnum } from "~/types/api";

export const PrivacyNoticesTable = () => {
  const router = useRouter();
  // Subscribe to get all privacy notices
  const page = useAppSelector(selectPage);
  const pageSize = useAppSelector(selectPageSize);
  const { isLoading } = useGetAllPrivacyNoticesQuery({ page, size: pageSize });

  const privacyNotices = useAppSelector(selectAllPrivacyNotices);
  // Permissions
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.PRIVACY_NOTICE_UPDATE,
  ]);
  const handleRowClick = ({ id }: PrivacyNoticeResponse) => {
    if (userCanUpdate) {
      router.push(`${PRIVACY_NOTICES_ROUTE}/${id}`);
    }
  };

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
        button={
          <Button
            size="sm"
            variant="outline"
            fontWeight="semibold"
            minWidth="auto"
          >
            <NextLink href={SYSTEM_ROUTE}>Set up data uses</NextLink>
          </Button>
        }
      />
    );
  }
  return (
    <FidesTable<PrivacyNoticeResponse>
      columns={columns}
      data={privacyNotices}
      onRowClick={userCanUpdate ? handleRowClick : undefined}
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
  );
};
