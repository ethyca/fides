import {
  AntButton as Button,
  AntColumnsType as ColumnsType,
  AntFlex as Flex,
  AntMessage as message,
  AntTable as Table,
  AntTypography,
  ConfirmationModal,
} from "fidesui";
import { useMemo, useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import Restrict, { useHasPermission } from "~/features/common/Restrict";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import {
  getCustomFieldType,
  RESOURCE_TYPE_MAP,
} from "~/features/custom-fields/constants";
import CustomFieldModalV2 from "~/features/custom-fields/v2/CustomFieldModalV2";
import EnableCustomFieldCellV2 from "~/features/custom-fields/v2/EnableCustomFieldCellV2";
import {
  useDeleteCustomFieldDefinitionMutation,
  useGetAllCustomFieldDefinitionsQuery,
} from "~/features/plus/plus.slice";
import {
  CustomFieldDefinitionWithId,
  ResourceTypes,
  ScopeRegistryEnum,
} from "~/types/api";

const DELETE_CUSTOM_FIELD_MSG_KEY = "delete-custom-field-msg";

const useCustomFieldsTable = () => {
  const tableState = useTableState({
    pagination: { defaultPageSize: 25, pageSizeOptions: [10, 25, 50] },
    // TODO: search not searching
    search: { defaultSearchQuery: "" },
  });

  const { data, isLoading, error } = useGetAllCustomFieldDefinitionsQuery();

  const [messageApi, messageContext] = message.useMessage();

  const [deleteCustomField] = useDeleteCustomFieldDefinitionMutation();

  if (error) {
    // TODO: do something
  }

  const { tableProps } = useAntTable(tableState, {
    dataSource: data || [],
    totalRows: data?.length || 0,
    isLoading,
  });

  const [formModalIsOpen, setFormModalIsOpen] = useState(false);
  const [deleteModalIsOpen, setDeleteModalIsOpen] = useState(false);

  const [activeField, setActiveField] = useState<
    CustomFieldDefinitionWithId | undefined
  >();

  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.CUSTOM_FIELD_UPDATE,
  ]);

  const userCanDelete = useHasPermission([
    ScopeRegistryEnum.CUSTOM_FIELD_DELETE,
  ]);

  const showActions = userCanUpdate || userCanDelete;

  const handleEditClick = (record: CustomFieldDefinitionWithId) => {
    setActiveField(record);
    setFormModalIsOpen(true);
  };

  const deleteSelectedField = async () => {
    if (!activeField || !userCanDelete) {
      return;
    }

    messageApi.open({
      key: DELETE_CUSTOM_FIELD_MSG_KEY,
      type: "loading",
      content: `Deleting ${activeField.name}...`,
    });

    const result = await deleteCustomField({ id: activeField.id! });
    if (isErrorResult(result)) {
      messageApi.open({
        key: DELETE_CUSTOM_FIELD_MSG_KEY,
        type: "error",
        content: getErrorMessage(result.error),
      });
      return;
    }
    messageApi.open({
      key: DELETE_CUSTOM_FIELD_MSG_KEY,
      type: "success",
      content: "Field deleted successfully",
    });
    setDeleteModalIsOpen(false);
  };

  const handleDeleteClick = (record: CustomFieldDefinitionWithId) => {
    setActiveField(record);
    setDeleteModalIsOpen(true);
  };

  const handleCloseFormModal = () => {
    setFormModalIsOpen(false);
    setActiveField(undefined);
  };

  const handleCloseDeleteModal = () => {
    setDeleteModalIsOpen(false);
    setActiveField(undefined);
  };

  const columns: ColumnsType<CustomFieldDefinitionWithId> = useMemo(
    () => [
      {
        title: "Name",
        dataIndex: "name",
        key: "name",
      },
      {
        title: "Description",
        dataIndex: "description",
        key: "description",
      },
      {
        title: "Field Type",
        dataIndex: "field_type",
        key: "field_type",
        render: (_: any, record: CustomFieldDefinitionWithId) =>
          getCustomFieldType(record),
      },
      {
        title: "Location",
        dataIndex: "resource_type",
        key: "resource_type",
        render: (value: ResourceTypes) => RESOURCE_TYPE_MAP.get(value) || value,
      },
      {
        title: "Enable",
        dataIndex: "active",
        key: "active",
        hidden: !userCanUpdate,
        render: (_: any, record: CustomFieldDefinitionWithId) => (
          <EnableCustomFieldCellV2 field={record} isDisabled={!userCanUpdate} />
        ),
      },
      {
        title: "Actions",
        key: "actions",
        render: (_: any, record: CustomFieldDefinitionWithId) => (
          <Flex gap="middle">
            <Button size="small" onClick={() => handleEditClick(record)}>
              Edit
            </Button>
            <Restrict scopes={[ScopeRegistryEnum.CUSTOM_FIELD_DELETE]}>
              <Button size="small" onClick={() => handleDeleteClick(record)}>
                Delete
              </Button>
            </Restrict>
          </Flex>
        ),
        hidden: !showActions,
        width: 96,
      },
    ],
    [showActions, userCanUpdate],
  );

  return {
    tableProps,
    columns,
    searchQuery: tableState.searchQuery,
    updateSearch: tableState.updateSearch,
    formModalIsOpen,
    handleOpenFormModal: () => setFormModalIsOpen(true),
    handleCloseFormModal,
    deleteModalIsOpen,
    handleCloseDeleteModal,
    deleteSelectedField,
    activeField,
    messageContext,
  };
};

export const CustomFieldsTableV2 = () => {
  const {
    tableProps,
    columns,
    searchQuery,
    updateSearch,
    formModalIsOpen,
    handleOpenFormModal,
    handleCloseFormModal,
    deleteModalIsOpen,
    handleCloseDeleteModal,
    deleteSelectedField,
    activeField,
    messageContext,
  } = useCustomFieldsTable();

  return (
    <Flex vertical gap="middle">
      <Flex justify="space-between">
        {messageContext}
        <DebouncedSearchInput
          value={searchQuery}
          onChange={updateSearch}
          placeholder="Search custom fields..."
        />
        <CustomFieldModalV2
          open={formModalIsOpen}
          field={activeField}
          onClose={handleCloseFormModal}
          centered
        />
        <ConfirmationModal
          isOpen={deleteModalIsOpen}
          onClose={handleCloseDeleteModal}
          onConfirm={deleteSelectedField}
          title="Delete custom field"
          message={
            <AntTypography.Text>
              Are you sure you want to delete{" "}
              <strong>{activeField?.name}</strong>? This action cannot be
              undone.
            </AntTypography.Text>
          }
          isCentered
        />
        <Button onClick={handleOpenFormModal} type="primary">
          Add custom field
        </Button>
      </Flex>
      <Table {...tableProps} columns={columns} />
    </Flex>
  );
};
