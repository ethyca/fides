import { Box, Heading, Text } from "@fidesui/react";
import type { NextPage } from "next";

import { useAppSelector } from "~/app/hooks";
import Layout from "~/features/common/Layout";
import {
  selectAllCustomFieldDefinitions,
  useGetAllCustomFieldDefinitionsQuery,
  useUpdateCustomFieldDefinitionMutation,
} from "~/features/plus/plus.slice";
import { useHasPermission } from "common/Restrict";
import { CustomFieldDefinitionWithId, ScopeRegistryEnum } from "~/types/api";
import { Column } from "react-table";
import { useMemo } from "react";
import {
  DateCell,
  EnableCell,
  MechanismCell,
  MultiTagCell,
  TitleCell,
  WrappedCell,
} from "common/table/cells";
import { FidesTable } from "common/table/FidesTable";

const CustomFields: NextPage = () => {
  useGetAllCustomFieldDefinitionsQuery();
  const customFields = useAppSelector(selectAllCustomFieldDefinitions);
  const [updateCustomFieldDefinitionTrigger] =
    useUpdateCustomFieldDefinitionMutation();

  // // Permissions
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.CUSTOM_FIELD_UPDATE,
  ]);
  //
  const columns: Column<CustomFieldDefinitionWithId>[] = useMemo(
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
        onToggle: updateCustomFieldDefinitionTrigger,
      },
    ],
    [updateCustomFieldDefinitionTrigger, userCanUpdate]
  );

  return (
    <Layout title="Custom fields">
      <Box data-testid="custom-fields-management">
        <Heading marginBottom={4} fontSize="2xl">
          Manage custom fields
        </Heading>
        <Box maxWidth="600px">
          <Text marginBottom={10} fontSize="sm">
            Custom fields provide organizations with the capability to capture
            metrics that are unique to their specific needs, allowing them to
            create customized reports. These fields can be added to either
            systems or elements within a taxonomy, and once added, they become
            reportable fields that are visible on the data map.
          </Text>
        </Box>
        <Box background="gray.50" padding={2}>
          <FidesTable<CustomFieldDefinitionWithId>
            columns={columns}
            data={customFields}
            userCanUpdate={userCanUpdate}
            redirectRoute={""}
            createScope={ScopeRegistryEnum.CUSTOM_FIELD_CREATE}
            tableType={"custom field"}
          />
        </Box>
      </Box>
    </Layout>
  );
};
export default CustomFields;
