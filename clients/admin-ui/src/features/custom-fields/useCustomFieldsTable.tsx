import {
  AntButton as Button,
  AntColumnsType as ColumnsType,
  AntFlex as Flex,
} from "fidesui";
import { useRouter } from "next/router";
import { useMemo } from "react";

import { CUSTOM_FIELDS_ROUTE } from "~/features/common/nav/routes";
import { useHasPermission } from "~/features/common/Restrict";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { RESOURCE_TYPE_MAP } from "~/features/custom-fields/constants";
import EnableCustomFieldCellV2 from "~/features/custom-fields/EnableCustomFieldCell";
import { getCustomFieldTypeLabel } from "~/features/custom-fields/utils";
import { useGetAllCustomFieldDefinitionsQuery } from "~/features/plus/plus.slice";
import {
  CustomFieldDefinitionWithId,
  ResourceTypes,
  ScopeRegistryEnum,
} from "~/types/api";

const useCustomFieldsTable = () => {
  const tableState = useTableState({
    pagination: { defaultPageSize: 25, pageSizeOptions: [10, 25, 50] },
    // TODO: search not searching
    search: { defaultSearchQuery: "" },
  });

  const router = useRouter();

  const { data, isLoading } = useGetAllCustomFieldDefinitionsQuery();

  const { tableProps } = useAntTable(tableState, {
    dataSource: data || [],
    totalRows: data?.length || 0,
    isLoading,
  });

  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.CUSTOM_FIELD_UPDATE,
  ]);

  const showActions = userCanUpdate;

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
        title: "Type",
        dataIndex: "field_type",
        key: "field_type",
        render: (_: any, record: CustomFieldDefinitionWithId) =>
          getCustomFieldTypeLabel(record),
      },
      {
        title: "Applies to",
        dataIndex: "resource_type",
        key: "resource_type",
        render: (value: ResourceTypes) => RESOURCE_TYPE_MAP.get(value) || value,
      },
      {
        title: "Enabled",
        dataIndex: "active",
        key: "active",
        hidden: !userCanUpdate,
        render: (_: any, record: CustomFieldDefinitionWithId) => (
          <EnableCustomFieldCellV2 field={record} isDisabled={!userCanUpdate} />
        ),
        width: 96,
      },
      {
        title: "Actions",
        key: "actions",
        render: (_: any, record: CustomFieldDefinitionWithId) => (
          <Flex gap="middle">
            <Button
              size="small"
              onClick={() => router.push(`${CUSTOM_FIELDS_ROUTE}/${record.id}`)}
              data-testid="edit-btn"
            >
              Edit
            </Button>
          </Flex>
        ),
        hidden: !showActions,
        width: 96,
      },
    ],
    [router, showActions, userCanUpdate],
  );

  return {
    tableProps,
    columns,
    searchQuery: tableState.searchQuery,
    updateSearch: tableState.updateSearch,
    onAddClick: () => router.push(`${CUSTOM_FIELDS_ROUTE}/new`),
  };
};

export default useCustomFieldsTable;
