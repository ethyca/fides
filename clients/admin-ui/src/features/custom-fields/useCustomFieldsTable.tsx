import { Button, ColumnsType, Flex } from "fidesui";
import { useRouter } from "next/router";
import { useMemo } from "react";

import { LegacyResourceTypes } from "~/features/common/custom-fields";
import { CUSTOM_FIELDS_ROUTE } from "~/features/common/nav/routes";
import { useHasPermission } from "~/features/common/Restrict";
import { EllipsisCell } from "~/features/common/table/cells/EllipsisCell";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import TagCell from "~/features/common/table/cells/TagCell";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import EnableCustomFieldCellV2 from "~/features/custom-fields/EnableCustomFieldCell";
import { useGetAllCustomFieldDefinitionsQuery } from "~/features/plus/plus.slice";
import { TaxonomyTypeEnum } from "~/features/taxonomy/constants";
import { useGetCustomTaxonomiesQuery } from "~/features/taxonomy/taxonomy.slice";
import { CustomFieldDefinitionWithId, ScopeRegistryEnum } from "~/types/api";

const FIELD_TYPE_LABEL_MAP = {
  [TaxonomyTypeEnum.DATA_CATEGORY]: "Data categories",
  [TaxonomyTypeEnum.DATA_USE]: "Data use field",
  [TaxonomyTypeEnum.DATA_SUBJECT]: "Data subjects",
  [TaxonomyTypeEnum.SYSTEM_GROUP]: "System groups",
};

const LOCATION_LABEL_MAP = {
  [LegacyResourceTypes.SYSTEM]: "System",
  [LegacyResourceTypes.DATA_USE]: "Taxonomy data use",
  [LegacyResourceTypes.DATA_CATEGORY]: "Data category",
  [LegacyResourceTypes.DATA_SUBJECT]: "Data subject",
  [LegacyResourceTypes.PRIVACY_DECLARATION]: "System data use",
};

const useCustomFieldsTable = () => {
  const tableState = useTableState({
    pagination: { defaultPageSize: 25, pageSizeOptions: [10, 25, 50] },
    search: { defaultSearchQuery: "" },
  });

  const router = useRouter();

  const { data, isLoading } = useGetAllCustomFieldDefinitionsQuery();

  const { data: customTaxonomies } = useGetCustomTaxonomiesQuery();

  const { tableProps } = useAntTable(tableState, {
    dataSource: data || [],
    totalRows: data?.length || 0,
    isLoading,
    customTableProps: {
      layout: "fixed",
      sticky: {
        offsetHeader: 40,
      },
    },
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
        filteredValue: tableState.searchQuery ? [tableState.searchQuery] : null,
        onFilter: (value, record) =>
          record.name.toLowerCase().includes(value.toString().toLowerCase()),
        render: (_, { id, name }) => (
          <LinkCell href={`${CUSTOM_FIELDS_ROUTE}/${id}`}>{name}</LinkCell>
        ),
      },
      {
        title: "Description",
        dataIndex: "description",
        key: "description",
        render: (text: string) => (
          <EllipsisCell className="w-96">{text}</EllipsisCell>
        ),
        width: 384,
      },
      {
        title: "Type",
        dataIndex: "field_type",
        key: "field_type",
        render: (_: any, record: CustomFieldDefinitionWithId) => {
          let label: string;
          if (record.field_type in FIELD_TYPE_LABEL_MAP) {
            label = FIELD_TYPE_LABEL_MAP[record.field_type as TaxonomyTypeEnum];
          } else {
            label =
              customTaxonomies?.find(
                (taxonomy) => taxonomy.fides_key === record.field_type,
              )?.name ?? record.field_type;
          }
          return <TagCell value={label} />;
        },
      },
      {
        title: "Applies to",
        dataIndex: "resource_type",
        key: "resource_type",
        render: (_, { resource_type }) => {
          let label: string;
          if (resource_type in LOCATION_LABEL_MAP) {
            label = LOCATION_LABEL_MAP[resource_type as LegacyResourceTypes];
          } else {
            label =
              customTaxonomies?.find(
                (taxonomy) => taxonomy.fides_key === resource_type,
              )?.name ?? resource_type;
          }
          return <TagCell value={label} />;
        },
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
    [
      customTaxonomies,
      router,
      showActions,
      tableState.searchQuery,
      userCanUpdate,
    ],
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
