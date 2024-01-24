import { Button, Flex, Spinner } from "@fidesui/react";
import { PRIVACY_NOTICES_ROUTE } from "common/nav/v2/routes";
import Restrict, { useHasPermission } from "common/Restrict";
import {
  DateCell,
  FidesTable,
  FidesTableFooter,
  TitleCell,
} from "common/table";
import NextLink from "next/link";
import { useRouter } from "next/router";
import React, { useMemo } from "react";
import { Column } from "react-table";

import { useAppSelector } from "~/app/hooks";
import {
  EnablePrivacyNoticeCell,
  FrameworkCell,
  LocationCell,
  MechanismCell,
  PrivacyNoticeStatusCell,
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

  const columns: Column<PrivacyNoticeResponse>[] = useMemo(() => {
    const noticeColumns: Column<PrivacyNoticeResponse>[] = [
      {
        Header: "Title",
        accessor: "name",
        Cell: TitleCell,
      },
      {
        Header: "Mechanism",
        accessor: "consent_mechanism",
        Cell: MechanismCell,
      },
      { Header: "Locations", accessor: "regions", Cell: LocationCell },
      { Header: "Last update", accessor: "updated_at", Cell: DateCell },
      {
        Header: "Status",
        Cell: PrivacyNoticeStatusCell,
      },
      {
        Header: "Framework",
        accessor: "framework",
        Cell: FrameworkCell,
      },
      {
        Header: "Enable",
        accessor: "disabled",
        Cell: EnablePrivacyNoticeCell,
      },
    ];
    // Only render the "Enable" column with toggle if user has permission to toggle
    if (userCanUpdate) {
      return noticeColumns;
    }
    return noticeColumns.filter((c) => c.accessor !== "disabled");
  }, [userCanUpdate]);

  if (isLoading) {
    return (
      <Flex height="100%" justifyContent="center" alignItems="center">
        <Spinner />
      </Flex>
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
