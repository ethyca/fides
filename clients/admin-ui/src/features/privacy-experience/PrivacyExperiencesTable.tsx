import { Box, Button, Flex, Spinner, Stack } from "@fidesui/react";
import { PRIVACY_EXPERIENCE_ROUTE, SYSTEM_ROUTE } from "common/nav/v2/routes";
import { useHasPermission } from "common/Restrict";
import { DateCell, FidesTable } from "common/table";
import EmptyTableState from "common/table/EmptyTableState";
import NextLink from "next/link";
import { useRouter } from "next/router";
import React, { useMemo } from "react";
import { Column } from "react-table";

import { useAppSelector } from "~/app/hooks";
import {
  ComponentCell,
  EnablePrivacyExperienceCell,
  LocationCell,
} from "~/features/privacy-experience/cells";
import {
  selectAllExperienceConfigs,
  selectPage,
  selectPageSize,
  useGetAllExperienceConfigsQuery,
} from "~/features/privacy-experience/privacy-experience.slice";
import { ExperienceConfigResponse, ScopeRegistryEnum } from "~/types/api";

import JavaScriptTag from "./JavaScriptTag";

const PrivacyExperiencesTable = () => {
  const router = useRouter();
  // Subscribe to get all privacy experiences
  const page = useAppSelector(selectPage);
  const pageSize = useAppSelector(selectPageSize);
  const { isLoading } = useGetAllExperienceConfigsQuery({
    page,
    size: pageSize,
  });
  const privacyExperiences = useAppSelector(selectAllExperienceConfigs);
  // Permissions
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.PRIVACY_EXPERIENCE_UPDATE,
  ]);
  const handleRowClick = ({ id }: ExperienceConfigResponse) => {
    if (userCanUpdate) {
      router.push(`${PRIVACY_EXPERIENCE_ROUTE}/${id}`);
    }
  };

  const columns: Column<ExperienceConfigResponse>[] = useMemo(
    () => [
      { Header: "Location", accessor: "regions", Cell: LocationCell },
      {
        Header: "Component",
        accessor: "component",
        Cell: ComponentCell,
      },
      { Header: "Last update", accessor: "updated_at", Cell: DateCell },
      {
        Header: "Enable",
        accessor: "disabled",
        disabled: !userCanUpdate,
        Cell: EnablePrivacyExperienceCell,
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

  if (privacyExperiences.length === 0) {
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
    <Stack spacing={3}>
      <Box alignSelf="end">
        <JavaScriptTag />
      </Box>
      <FidesTable<ExperienceConfigResponse>
        columns={columns}
        data={privacyExperiences}
        onRowClick={userCanUpdate ? handleRowClick : undefined}
      />
    </Stack>
  );
};

export default PrivacyExperiencesTable;
