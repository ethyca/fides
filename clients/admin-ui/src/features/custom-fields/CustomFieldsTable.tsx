import {
  Box,
  Button,
  Flex,
  Spinner,
  Text,
  useDisclosure,
  useToast,
} from "@fidesui/react";
import Restrict, { useHasPermission } from "common/Restrict";
import {
  FidesTable,
  FidesTableFooter,
  TitleCell,
  WrappedCell,
} from "common/table";
import EmptyTableState from "common/table/EmptyTableState";
import React, { useMemo, useState } from "react";
import { Column, Hooks } from "react-table";

import { useAppSelector } from "~/app/hooks";
import {
  selectAllCustomFieldDefinitions,
  useDeleteCustomFieldDefinitionMutation,
  useGetAllCustomFieldDefinitionsQuery,
} from "~/features/plus/plus.slice";
import { CustomFieldDefinitionWithId, ScopeRegistryEnum } from "~/types/api";

import { getErrorMessage, isErrorResult } from "../common/helpers";
import { errorToastParams, successToastParams } from "../common/toast";
import { EnableCustomFieldCell, FieldTypeCell, MoreActionsCell } from "./cells";
import { CustomFieldModal } from "./CustomFieldModal";

export const CustomFieldsTable = () => {
  const toast = useToast();
  const { isLoading } = useGetAllCustomFieldDefinitionsQuery();
  const customFields = useAppSelector(selectAllCustomFieldDefinitions);
  const [deleteCustomFieldDefinitionMutationTrigger] =
    useDeleteCustomFieldDefinitionMutation();
  const { isOpen, onClose, onOpen } = useDisclosure();

  const [activeCustomField, setActiveCustomField] = useState<
    CustomFieldDefinitionWithId | undefined
  >(undefined);

  // Permissions
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.CUSTOM_FIELD_UPDATE,
  ]);
  const userCanDelete = useHasPermission([
    ScopeRegistryEnum.CUSTOM_FIELD_DELETE,
  ]);

  const handleRowClick = (customField: CustomFieldDefinitionWithId) => {
    if (userCanUpdate) {
      setActiveCustomField(customField);
      onOpen();
    }
  };

  const handleDelete = async (customField: CustomFieldDefinitionWithId) => {
    if (userCanDelete && customField.id) {
      const result = await deleteCustomFieldDefinitionMutationTrigger({
        id: customField.id,
      });
      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
        return;
      }
      toast(successToastParams("Custom field deleted"));
    }
  };

  const tableHook = (hooks: Hooks<CustomFieldDefinitionWithId>) => {
    if (!userCanUpdate && !userCanDelete) {
      return;
    }
    hooks.visibleColumns.push((visibleColumns) => [
      ...visibleColumns,
      {
        id: "more-actions",
        Header: () => null,
        Cell: MoreActionsCell,
        width: "50px",
        onEdit: handleRowClick,
        onDelete: handleDelete,
      },
    ]);
  };

  const handleCloseModal = () => {
    setActiveCustomField(undefined);
    onClose();
  };

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
    <>
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
          showSearchBar
          onRowClick={userCanUpdate ? handleRowClick : undefined}
          customHooks={[tableHook]}
          footer={
            // +1 for total columns because our hook adds a column for the
            // more actions menu
            <FidesTableFooter totalColumns={columns.length + 1}>
              <Restrict
                scopes={[ScopeRegistryEnum.CUSTOM_FIELD_DEFINITION_CREATE]}
              >
                <Button
                  size="xs"
                  colorScheme="primary"
                  data-testid="add-custom-field-btn"
                  onClick={onOpen}
                >
                  Add a custom field +
                </Button>
              </Restrict>
            </FidesTableFooter>
          }
        />
        <CustomFieldModal
          customField={activeCustomField}
          isOpen={isOpen}
          onClose={handleCloseModal}
          isLoading={false}
        />
      </Box>
    </>
  );
};
