import { Box, Flex, Heading, Spinner, Text } from "@fidesui/react";
import { useHasPermission } from "common/Restrict";
import type { NextPage } from "next";
import React, { useMemo } from "react";
import { CellProps, Column } from "react-table";

import { useAppSelector } from "~/app/hooks";
import Layout from "~/features/common/Layout";
import {
  EnableCell,
  FieldTypeCell,
  TitleCell,
  WrappedCell,
} from "~/features/common/table/cells";
import EmptyTableState from "~/features/common/table/EmptyTableState";
import { FidesTable } from "~/features/common/table/FidesTable";
import {
  selectAllCustomFieldDefinitions,
  useGetAllCustomFieldDefinitionsQuery,
  useUpdateCustomFieldDefinitionMutation,
} from "~/features/plus/plus.slice";
import {
  CustomFieldDefinition,
  CustomFieldDefinitionWithId,
  ScopeRegistryEnum,
} from "~/types/api";

export const EnableCustomFieldCell = (
  cellProps: CellProps<CustomFieldDefinition, boolean>
) => {
  const [updateCustomFieldDefinitionTrigger] =
    useUpdateCustomFieldDefinitionMutation();
  const { row } = cellProps;

  const onToggle = async (toggle: boolean) => {
    await updateCustomFieldDefinitionTrigger({
      ...row.original,
      active: toggle,
    });
  };

  return (
    <EnableCell<CustomFieldDefinition>
      {...cellProps}
      onToggle={onToggle}
      title="Disable custom field"
      message="Are you sure you want to disable this custom field?"
    />
  );
}; // use this one in custom-fields/index.tsx column def

const CustomFields: NextPage = () => {
  const { isLoading } = useGetAllCustomFieldDefinitionsQuery();
  const customFields = useAppSelector(selectAllCustomFieldDefinitions);

  // Permissions
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.CUSTOM_FIELD_UPDATE,
  ]);
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
      { Header: "Field Type", accessor: "field_type", Cell: FieldTypeCell },
      { Header: "Locations", accessor: "resource_type", Cell: WrappedCell },
      {
        Header: "Enable",
        accessor: (row) => !row.active,
        disabled: !userCanUpdate,
        Cell: EnableCustomFieldCell,
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

  if (customFields.length === 0) {
    return (
      <EmptyTableState
        title="It looks like it’s your first time here!"
        buttonHref=""
        buttonText="Add a custom field"
        description={
          <>
            You haven’t created any custom fields yet. To create a custom field,
            click on the <strong>&quot;Add a custom field&quot;</strong> button
          </>
        }
      />
    );
  }

  return (
    <Layout title="Custom fields">
      <Box data-testid="custom-fields-management">
        <Heading marginBottom={4} fontSize="2xl">
          Manage custom fields
        </Heading>
        <Box maxWidth="600px">
          <Text marginBottom={10} fontSize="sm">
            {customFields.length > 0
              ? "Custom fields enable you to capture metrics specific to your organization and have those metrics appear in the data map and in reports."
              : "Custom fields provide organizations with the capability to capture metrics that are unique to their specific needs, allowing them to create customized reports. These fields can be added to either systems or elements within a taxonomy, and once added, they become reportable fields that are visible on the data map."}
          </Text>
        </Box>
        <Box padding={2} data-testid="custom-fields-page">
          <FidesTable<CustomFieldDefinitionWithId>
            columns={columns}
            data={customFields}
            userCanUpdate={userCanUpdate}
            redirectRoute=""
            showSearchBar
          />
        </Box>
      </Box>
    </Layout>
  );
};
export default CustomFields;
