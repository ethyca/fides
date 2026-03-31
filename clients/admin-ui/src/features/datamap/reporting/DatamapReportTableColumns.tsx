import {
  ColumnsType,
  CUSTOM_TAG_COLOR,
  Form,
  FormInstance,
  Input,
  MenuProps,
} from "fidesui";
import { isArray, snakeCase } from "lodash";
import { ReactNode } from "react";

import {
  ListExpandableCell,
  TagExpandableCell,
} from "~/features/common/table/cells";
import { expandCollapseAllMenuItems } from "~/features/common/table/cells/constants";
import { EllipsisCell } from "~/features/common/table/cells/EllipsisCell";
import { InteractiveTextCell } from "~/features/common/table/cells/InteractiveTextCell";
import { COLOR_VALUE_MAP } from "~/features/system/system-groups/colors";
import {
  CustomFieldDefinitionWithId,
  DATAMAP_GROUPING,
  Page_DatamapReport_,
  SystemGroup,
} from "~/types/api";

import { COLUMN_IDS, DEFAULT_COLUMN_NAMES } from "./constants";
import { DatamapReportRow, getGroupKey } from "./groupDatamapRows";
import { getColKey } from "./utils";

type MenuClickInfo = Parameters<NonNullable<MenuProps["onClick"]>>[0];

export const CUSTOM_FIELD_SYSTEM_PREFIX = "system_";
export const CUSTOM_FIELD_DATA_USE_PREFIX = "privacy_declaration_";

export interface DatamapReportColumnProps {
  onOpenSystemDrawer: (row: DatamapReportRow) => void;
  getDataUseDisplayName: (dataUseKey: string) => ReactNode;
  getDataCategoryDisplayName: (dataCategoryKey: string) => string | JSX.Element;
  getDataSubjectDisplayName: (dataSubjectKey: string) => ReactNode;
  datamapReport: Page_DatamapReport_ | undefined;
  customFields: CustomFieldDefinitionWithId[];
  systemGroups?: SystemGroup[];
  isRenaming?: boolean;
  groupBy?: string;
  columnNameMap: Record<string, string>;
  form?: FormInstance;
  expandedColumns: Record<string, boolean>;
  onToggleColumnExpand: (columnId: string, expanded: boolean) => void;
}

/**
 * Returns the expand/collapse header menu for a column, or an empty object
 * when column renaming is active (menus are hidden during rename).
 */
const expandCollapseMenu = (
  columnId: string,
  isRenaming: boolean,
  onToggleColumnExpand: (id: string, expanded: boolean) => void,
) =>
  !isRenaming
    ? {
        menu: {
          items: expandCollapseAllMenuItems,
          onClick: (e: MenuClickInfo) => {
            e.domEvent.stopPropagation();
            onToggleColumnExpand(columnId, e.key === "expand-all");
          },
        },
      }
    : {};

/**
 * Get the display title for a column, supporting inline renaming via Ant Form.
 */
const getColumnTitle = (
  columnId: string,
  columnNameMap: Record<string, string>,
  isRenaming: boolean,
  form?: FormInstance,
): ReactNode => {
  const displayName =
    columnNameMap[columnId] ||
    DEFAULT_COLUMN_NAMES[columnId as COLUMN_IDS] ||
    columnId;

  if (isRenaming && form) {
    return (
      <Form.Item name={columnId} noStyle>
        <Input
          size="small"
          placeholder={DEFAULT_COLUMN_NAMES[columnId as COLUMN_IDS] || columnId}
          onPressEnter={() => form.submit()}
          onClick={(e) => e.stopPropagation()}
          data-testid={`column-${columnId}-input`}
          style={{ minWidth: 100 }}
        />
      </Form.Item>
    );
  }
  return displayName;
};

const getCustomFieldColumns = (
  datamapReport: Page_DatamapReport_ | undefined,
  customFields: CustomFieldDefinitionWithId[],
  columnNameMap: Record<string, string>,
  isRenaming: boolean,
  expandedColumns: Record<string, boolean>,
  onToggleColumnExpand: (columnId: string, expanded: boolean) => void,
  form?: FormInstance,
): ColumnsType<DatamapReportRow> => {
  const datamapKeys = datamapReport?.items?.length
    ? Object.keys(datamapReport.items[0])
    : [];
  const defaultKeys = Object.values(COLUMN_IDS);
  const customFieldKeys = datamapKeys
    .filter((k) => !defaultKeys.includes(k as COLUMN_IDS))
    .filter(
      (k) =>
        k.startsWith(CUSTOM_FIELD_DATA_USE_PREFIX) ||
        k.startsWith(CUSTOM_FIELD_SYSTEM_PREFIX),
    );

  return customFieldKeys.map((key) => {
    const customField = customFields.find((cf) =>
      key.includes(snakeCase(cf.name)),
    );
    const isArrayField = customField?.field_type === "string[]";

    return {
      title:
        customField?.name ||
        getColumnTitle(key, columnNameMap, isRenaming, form), // Custom fields cannot be renamed, so we only care about the name and then we fall back to generating a title from the key if that's missing.
      dataIndex: key,
      key,
      render: (value: unknown) => {
        if (Array.isArray(value)) {
          return (
            <ListExpandableCell
              values={value.map(String)}
              valueSuffix={key}
              columnState={{ isExpanded: expandedColumns[key] }}
            />
          );
        }
        return (
          <EllipsisCell>
            {value !== null && value !== undefined ? String(value) : ""}
          </EllipsisCell>
        );
      },
      ...(isArrayField
        ? expandCollapseMenu(key, isRenaming, onToggleColumnExpand)
        : {}),
    };
  });
};

export const getDatamapReportColumns = ({
  onOpenSystemDrawer,
  getDataUseDisplayName,
  getDataCategoryDisplayName,
  getDataSubjectDisplayName,
  datamapReport,
  customFields,
  systemGroups = [],
  isRenaming = false,
  groupBy,
  columnNameMap,
  form,
  expandedColumns,
  onToggleColumnExpand,
}: DatamapReportColumnProps): ColumnsType<DatamapReportRow> => {
  const customFieldColumns = getCustomFieldColumns(
    datamapReport,
    customFields,
    columnNameMap,
    isRenaming,
    expandedColumns,
    onToggleColumnExpand,
    form,
  );

  const getSystemGroupColor = (
    fidesKey: string,
  ): CUSTOM_TAG_COLOR | undefined => {
    const systemGroup = systemGroups.find(
      (group) => group.fides_key === fidesKey,
    );
    return systemGroup?.label_color
      ? COLOR_VALUE_MAP[systemGroup.label_color]
      : undefined;
  };

  const getDominantColor = (
    groupKeys: string[],
  ): CUSTOM_TAG_COLOR | undefined => {
    if (!groupKeys || groupKeys.length === 0) {
      return undefined;
    }
    if (groupKeys.length === 1) {
      return getSystemGroupColor(groupKeys[0]);
    }
    return undefined;
  };

  const title = (id: string) =>
    getColumnTitle(id, columnNameMap, isRenaming, form);

  const menu = (columnId: string) =>
    expandCollapseMenu(columnId, isRenaming, onToggleColumnExpand);

  const baseColumns: ColumnsType<DatamapReportRow> = [
    {
      title: title(COLUMN_IDS.SYSTEM_NAME),
      dataIndex: "system_name",
      key: COLUMN_IDS.SYSTEM_NAME,
      render: (value: string, record: DatamapReportRow) => (
        <InteractiveTextCell onClick={() => onOpenSystemDrawer(record)}>
          {value}
        </InteractiveTextCell>
      ),
      className: `column-${COLUMN_IDS.SYSTEM_NAME}`,
    },
    {
      title: title(COLUMN_IDS.DATA_USE),
      dataIndex: "data_uses",
      key: COLUMN_IDS.DATA_USE,
      render: (value: string | string[] | null) => {
        if (!value) {
          return null;
        }
        const displayValues = isArray(value)
          ? value.map((v) => ({
              label: getDataUseDisplayName(v),
              key: v,
            }))
          : [{ label: getDataUseDisplayName(value), key: value }];
        return (
          <TagExpandableCell
            values={displayValues}
            tagProps={{ color: "white" }}
            columnState={{ isExpanded: expandedColumns[COLUMN_IDS.DATA_USE] }}
          />
        );
      },
      className: `column-${COLUMN_IDS.DATA_USE}`,
    },
    {
      title: title(COLUMN_IDS.DATA_CATEGORY),
      dataIndex: "data_categories",
      key: COLUMN_IDS.DATA_CATEGORY,
      render: (value: string | string[] | null) => {
        if (!value || (Array.isArray(value) && value.length === 0)) {
          return null;
        }
        const values = isArray(value)
          ? value.map((v) => ({
              label: getDataCategoryDisplayName(v),
              key: v,
            }))
          : [{ label: getDataCategoryDisplayName(value), key: value }];
        return (
          <TagExpandableCell
            values={values}
            columnState={{
              isExpanded: expandedColumns[COLUMN_IDS.DATA_CATEGORY],
            }}
          />
        );
      },
      ...menu(COLUMN_IDS.DATA_CATEGORY),
      className: `column-${COLUMN_IDS.DATA_CATEGORY}`,
    },
    {
      title: title(COLUMN_IDS.DATA_SUBJECT),
      dataIndex: "data_subjects",
      key: COLUMN_IDS.DATA_SUBJECT,
      render: (value: string[] | null) => {
        if (!value) {
          return null;
        }
        const displayValues = isArray(value)
          ? value.map((v) => ({
              label: getDataSubjectDisplayName(v),
              key: v,
            }))
          : [{ label: getDataSubjectDisplayName(value), key: value }];
        return (
          <TagExpandableCell
            values={displayValues}
            tagProps={{ color: "white" }}
            columnState={{
              isExpanded: expandedColumns[COLUMN_IDS.DATA_SUBJECT],
            }}
          />
        );
      },
      ...menu(COLUMN_IDS.DATA_SUBJECT),
      className: `column-${COLUMN_IDS.DATA_SUBJECT}`,
    },
    {
      title: title(COLUMN_IDS.LEGAL_NAME),
      dataIndex: "legal_name",
      key: COLUMN_IDS.LEGAL_NAME,
      render: (value: string | null) => (
        <EllipsisCell>{value ?? ""}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.DPO),
      dataIndex: "dpo",
      key: COLUMN_IDS.DPO,
      render: (value: string | null) => (
        <EllipsisCell>{value ?? ""}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.LEGAL_BASIS_FOR_PROCESSING),
      dataIndex: "legal_basis_for_processing",
      key: COLUMN_IDS.LEGAL_BASIS_FOR_PROCESSING,
      render: (value: string | null) => (
        <EllipsisCell>{value ?? ""}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.ADMINISTRATING_DEPARTMENT),
      dataIndex: "administrating_department",
      key: COLUMN_IDS.ADMINISTRATING_DEPARTMENT,
      render: (value: string | null) => (
        <EllipsisCell>{value ?? ""}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.COOKIE_MAX_AGE_SECONDS),
      dataIndex: "cookie_max_age_seconds",
      key: COLUMN_IDS.COOKIE_MAX_AGE_SECONDS,
      render: (value: number | null) => (
        <EllipsisCell>
          {value !== null && value !== undefined ? String(value) : ""}
        </EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.PRIVACY_POLICY),
      dataIndex: "privacy_policy",
      key: COLUMN_IDS.PRIVACY_POLICY,
      render: (value: string | null) => (
        <EllipsisCell>{value ?? ""}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.LEGAL_ADDRESS),
      dataIndex: "legal_address",
      key: COLUMN_IDS.LEGAL_ADDRESS,
      render: (value: string | null) => (
        <EllipsisCell>{value ?? ""}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.COOKIE_REFRESH),
      dataIndex: "cookie_refresh",
      key: COLUMN_IDS.COOKIE_REFRESH,
      render: (value: boolean | null) => (
        <EllipsisCell>{String(value ?? "")}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.DATA_SECURITY_PRACTICES),
      dataIndex: "data_security_practices",
      key: COLUMN_IDS.DATA_SECURITY_PRACTICES,
      render: (value: string | null) => (
        <EllipsisCell>{value ?? ""}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.DATA_SHARED_WITH_THIRD_PARTIES),
      dataIndex: "data_shared_with_third_parties",
      key: COLUMN_IDS.DATA_SHARED_WITH_THIRD_PARTIES,
      render: (value: boolean | null) => (
        <EllipsisCell>
          {value !== null && value !== undefined ? String(value) : ""}
        </EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.PROCESSES_SPECIAL_CATEGORY_DATA),
      dataIndex: "processes_special_category_data",
      key: COLUMN_IDS.PROCESSES_SPECIAL_CATEGORY_DATA,
      render: (value: string | null) => (
        <EllipsisCell>{value ?? ""}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.DATA_STEWARDS),
      dataIndex: "data_stewards",
      key: COLUMN_IDS.DATA_STEWARDS,
      render: (value: string[] | null) => (
        <ListExpandableCell
          values={value ?? []}
          valueSuffix="data stewards"
          columnState={{
            isExpanded: expandedColumns[COLUMN_IDS.DATA_STEWARDS],
          }}
        />
      ),
      ...menu(COLUMN_IDS.DATA_STEWARDS),
    },
    {
      title: title(COLUMN_IDS.DECLARATION_NAME),
      dataIndex: "declaration_name",
      key: COLUMN_IDS.DECLARATION_NAME,
      render: (value: string | null) => (
        <EllipsisCell>{value ?? ""}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.DOES_INTERNATIONAL_TRANSFERS),
      dataIndex: "does_international_transfers",
      key: COLUMN_IDS.DOES_INTERNATIONAL_TRANSFERS,
      render: (value: boolean | null) => (
        <EllipsisCell>{String(value ?? "")}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.DPA_LOCATION),
      dataIndex: "dpa_location",
      key: COLUMN_IDS.DPA_LOCATION,
      render: (value: string | null) => (
        <EllipsisCell>{value ?? ""}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.DESTINATIONS),
      dataIndex: "egress",
      key: COLUMN_IDS.DESTINATIONS,
      render: (value: string[] | null) => (
        <ListExpandableCell
          values={value ?? []}
          valueSuffix="destinations"
          columnState={{
            isExpanded: expandedColumns[COLUMN_IDS.DESTINATIONS],
          }}
        />
      ),
      ...menu(COLUMN_IDS.DESTINATIONS),
    },
    {
      title: title(COLUMN_IDS.EXEMPT_FROM_PRIVACY_REGULATIONS),
      dataIndex: "exempt_from_privacy_regulations",
      key: COLUMN_IDS.EXEMPT_FROM_PRIVACY_REGULATIONS,
      render: (value: boolean | null) => (
        <EllipsisCell>{String(value ?? "")}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.FEATURES),
      dataIndex: "features",
      key: COLUMN_IDS.FEATURES,
      render: (value: string[] | null) => (
        <ListExpandableCell
          values={value ?? []}
          valueSuffix="features"
          columnState={{ isExpanded: expandedColumns[COLUMN_IDS.FEATURES] }}
        />
      ),
      ...menu(COLUMN_IDS.FEATURES),
    },
    {
      title: title(COLUMN_IDS.FIDES_KEY),
      dataIndex: "fides_key",
      key: COLUMN_IDS.FIDES_KEY,
      render: (value: string) => <EllipsisCell>{value}</EllipsisCell>,
    },
    {
      title: title(COLUMN_IDS.FLEXIBLE_LEGAL_BASIS_FOR_PROCESSING),
      dataIndex: "flexible_legal_basis_for_processing",
      key: COLUMN_IDS.FLEXIBLE_LEGAL_BASIS_FOR_PROCESSING,
      render: (value: boolean | null) => (
        <EllipsisCell>
          {value !== null && value !== undefined ? String(value) : ""}
        </EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.IMPACT_ASSESSMENT_LOCATION),
      dataIndex: "impact_assessment_location",
      key: COLUMN_IDS.IMPACT_ASSESSMENT_LOCATION,
      render: (value: string | null) => (
        <EllipsisCell>{value ?? ""}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.SOURCES),
      dataIndex: "ingress",
      key: COLUMN_IDS.SOURCES,
      render: (value: string[] | null) => (
        <ListExpandableCell
          values={value ?? []}
          valueSuffix="sources"
          columnState={{ isExpanded: expandedColumns[COLUMN_IDS.SOURCES] }}
        />
      ),
      ...menu(COLUMN_IDS.SOURCES),
    },
    {
      title: title(COLUMN_IDS.JOINT_CONTROLLER_INFO),
      dataIndex: "joint_controller_info",
      key: COLUMN_IDS.JOINT_CONTROLLER_INFO,
      render: (value: string | null) => (
        <EllipsisCell>{value ?? ""}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.LEGAL_BASIS_FOR_PROFILING),
      dataIndex: "legal_basis_for_profiling",
      key: COLUMN_IDS.LEGAL_BASIS_FOR_PROFILING,
      render: (value: string[] | null) => (
        <ListExpandableCell
          values={value ?? []}
          valueSuffix="profiles"
          columnState={{
            isExpanded: expandedColumns[COLUMN_IDS.LEGAL_BASIS_FOR_PROFILING],
          }}
        />
      ),
      ...menu(COLUMN_IDS.LEGAL_BASIS_FOR_PROFILING),
    },
    {
      title: title(COLUMN_IDS.LEGAL_BASIS_FOR_TRANSFERS),
      dataIndex: "legal_basis_for_transfers",
      key: COLUMN_IDS.LEGAL_BASIS_FOR_TRANSFERS,
      render: (value: string[] | null) => (
        <ListExpandableCell
          values={value ?? []}
          valueSuffix="transfers"
          columnState={{
            isExpanded: expandedColumns[COLUMN_IDS.LEGAL_BASIS_FOR_TRANSFERS],
          }}
        />
      ),
      ...menu(COLUMN_IDS.LEGAL_BASIS_FOR_TRANSFERS),
    },
    {
      title: title(COLUMN_IDS.LEGITIMATE_INTEREST_DISCLOSURE_URL),
      dataIndex: "legitimate_interest_disclosure_url",
      key: COLUMN_IDS.LEGITIMATE_INTEREST_DISCLOSURE_URL,
      render: (value: string | null) => (
        <EllipsisCell>{value ?? ""}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.PROCESSES_PERSONAL_DATA),
      dataIndex: "processes_personal_data",
      key: COLUMN_IDS.PROCESSES_PERSONAL_DATA,
      render: (value: boolean | null) => (
        <EllipsisCell>{String(value ?? "")}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.REASON_FOR_EXEMPTION),
      dataIndex: "reason_for_exemption",
      key: COLUMN_IDS.REASON_FOR_EXEMPTION,
      render: (value: string | null) => (
        <EllipsisCell>{value ?? ""}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.REQUIRES_DATA_PROTECTION_ASSESSMENTS),
      dataIndex: "requires_data_protection_assessments",
      key: COLUMN_IDS.REQUIRES_DATA_PROTECTION_ASSESSMENTS,
      render: (value: boolean | null) => (
        <EllipsisCell>{String(value ?? "")}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.RESPONSIBILITY),
      dataIndex: "responsibility",
      key: COLUMN_IDS.RESPONSIBILITY,
      render: (value: string[] | null) => (
        <ListExpandableCell
          values={value ?? []}
          valueSuffix="responsibilities"
          columnState={{
            isExpanded: expandedColumns[COLUMN_IDS.RESPONSIBILITY],
          }}
        />
      ),
      ...menu(COLUMN_IDS.RESPONSIBILITY),
    },
    {
      title: title(COLUMN_IDS.RETENTION_PERIOD),
      dataIndex: "retention_period",
      key: COLUMN_IDS.RETENTION_PERIOD,
      render: (value: string | null) => (
        <EllipsisCell>{value ?? ""}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.SHARED_CATEGORIES),
      dataIndex: "shared_categories",
      key: COLUMN_IDS.SHARED_CATEGORIES,
      render: (value: string[] | null) => {
        if (!value || value.length === 0) {
          return null;
        }
        const displayValues = value.map((v) => ({
          label: v,
          key: v,
        }));
        return (
          <TagExpandableCell
            values={displayValues}
            tagProps={{ color: "white" }}
            columnState={{
              isExpanded: expandedColumns[COLUMN_IDS.SHARED_CATEGORIES],
            }}
          />
        );
      },
      ...menu(COLUMN_IDS.SHARED_CATEGORIES),
    },
    {
      title: title(COLUMN_IDS.SPECIAL_CATEGORY_LEGAL_BASIS),
      dataIndex: "special_category_legal_basis",
      key: COLUMN_IDS.SPECIAL_CATEGORY_LEGAL_BASIS,
      render: (value: string | null) => (
        <EllipsisCell>{value ?? ""}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.THIRD_PARTIES),
      dataIndex: "third_parties",
      key: COLUMN_IDS.THIRD_PARTIES,
      render: (value: string | null) => (
        <EllipsisCell>{value ?? ""}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.SYSTEM_UNDECLARED_DATA_CATEGORIES),
      dataIndex: "system_undeclared_data_categories",
      key: COLUMN_IDS.SYSTEM_UNDECLARED_DATA_CATEGORIES,
      render: (value: string[] | null) => {
        if (!value || value.length === 0) {
          return null;
        }
        const values = value.map((v) => ({
          label: getDataCategoryDisplayName(v),
          key: v,
        }));
        return (
          <TagExpandableCell
            values={values}
            columnState={{
              isExpanded:
                expandedColumns[COLUMN_IDS.SYSTEM_UNDECLARED_DATA_CATEGORIES],
            }}
          />
        );
      },
      ...menu(COLUMN_IDS.SYSTEM_UNDECLARED_DATA_CATEGORIES),
    },
    {
      title: title(COLUMN_IDS.DATA_USE_UNDECLARED_DATA_CATEGORIES),
      dataIndex: "data_use_undeclared_data_categories",
      key: COLUMN_IDS.DATA_USE_UNDECLARED_DATA_CATEGORIES,
      render: (value: string[] | null) => {
        if (!value || value.length === 0) {
          return null;
        }
        const values = value.map((v) => ({
          label: getDataCategoryDisplayName(v),
          key: v,
        }));
        return (
          <TagExpandableCell
            values={values}
            columnState={{
              isExpanded:
                expandedColumns[COLUMN_IDS.DATA_USE_UNDECLARED_DATA_CATEGORIES],
            }}
          />
        );
      },
      ...menu(COLUMN_IDS.DATA_USE_UNDECLARED_DATA_CATEGORIES),
    },
    {
      title: title(COLUMN_IDS.COOKIES),
      dataIndex: "cookies",
      key: COLUMN_IDS.COOKIES,
      render: (value: string[] | null) => (
        <ListExpandableCell
          values={value ?? []}
          valueSuffix="cookies"
          columnState={{ isExpanded: expandedColumns[COLUMN_IDS.COOKIES] }}
        />
      ),
      ...menu(COLUMN_IDS.COOKIES),
    },
    {
      title: title(COLUMN_IDS.USES_COOKIES),
      dataIndex: "uses_cookies",
      key: COLUMN_IDS.USES_COOKIES,
      render: (value: boolean | null) => (
        <EllipsisCell>{String(value ?? "")}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.USES_NON_COOKIE_ACCESS),
      dataIndex: "uses_non_cookie_access",
      key: COLUMN_IDS.USES_NON_COOKIE_ACCESS,
      render: (value: boolean | null) => (
        <EllipsisCell>{String(value ?? "")}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.USES_PROFILING),
      dataIndex: "uses_profiling",
      key: COLUMN_IDS.USES_PROFILING,
      render: (value: boolean | null) => (
        <EllipsisCell>{String(value ?? "")}</EllipsisCell>
      ),
    },
    {
      title: title(COLUMN_IDS.SYSTEM_GROUPS),
      dataIndex: "system_groups",
      key: COLUMN_IDS.SYSTEM_GROUPS,
      render: (value: string[] | null) => {
        if (!value || (Array.isArray(value) && value.length === 0)) {
          return null;
        }
        const groupKeys = Array.isArray(value) ? value : [value];
        const values = groupKeys.map((groupKey) => {
          const systemGroup = systemGroups.find(
            (sg) => sg.fides_key === groupKey,
          );
          return {
            label: systemGroup?.name || groupKey,
            key: groupKey,
            tagProps: {
              color: systemGroup?.label_color
                ? COLOR_VALUE_MAP[systemGroup.label_color]
                : undefined,
              bordered: false,
            },
          };
        });
        return <TagExpandableCell values={values} />;
      },
    },
  ];

  // System group specific columns
  const systemGroupColumns: ColumnsType<DatamapReportRow> = [];
  if (groupBy === DATAMAP_GROUPING.SYSTEM_GROUP) {
    systemGroupColumns.push(
      {
        title: title(COLUMN_IDS.SYSTEM_GROUP),
        dataIndex: "system_group_fides_key",
        key: COLUMN_IDS.SYSTEM_GROUP,
        render: (value: string | string[] | null) => {
          if (!value || (Array.isArray(value) && value.length === 0)) {
            return null;
          }
          const groupKeys = Array.isArray(value) ? value : [value];
          const groupNames = groupKeys.map(
            (groupKey) =>
              systemGroups.find((sg) => sg.fides_key === groupKey)?.name ||
              groupKey,
          );
          const dominantColor = getDominantColor(groupKeys);
          const displayValues = groupNames.map((name, idx) => ({
            label: name,
            key: groupKeys[idx],
          }));
          return (
            <TagExpandableCell
              values={displayValues}
              tagProps={{
                color: dominantColor ?? CUSTOM_TAG_COLOR.WHITE,
                bordered: false,
              }}
              columnState={{
                isExpanded: expandedColumns[COLUMN_IDS.SYSTEM_GROUP],
              }}
            />
          );
        },
        ...menu(COLUMN_IDS.SYSTEM_GROUP),
      },
      {
        title: title(COLUMN_IDS.SYSTEM_GROUP_DATA_USES),
        dataIndex: "system_group_data_uses",
        key: COLUMN_IDS.SYSTEM_GROUP_DATA_USES,
        render: (value: string | string[] | null) => {
          if (!value || (Array.isArray(value) && value.length === 0)) {
            return null;
          }
          const displayValues = isArray(value)
            ? value.map((v) => ({
                label: getDataUseDisplayName(v),
                key: v,
              }))
            : [{ label: getDataUseDisplayName(value), key: value }];
          return (
            <TagExpandableCell
              values={displayValues}
              tagProps={{ color: "white" }}
              columnState={{
                isExpanded: expandedColumns[COLUMN_IDS.SYSTEM_GROUP_DATA_USES],
              }}
            />
          );
        },
        ...menu(COLUMN_IDS.SYSTEM_GROUP_DATA_USES),
      },
    );
  }

  const allColumns = [
    ...baseColumns,
    ...systemGroupColumns,
    ...customFieldColumns,
  ];

  // Determine the grouping column key so we can apply rowSpan
  const groupingColKey = groupBy
    ? (getGroupKey(groupBy as DATAMAP_GROUPING) as string)
    : undefined;

  // Inject data-testid attributes and rowSpan for the grouping column
  return allColumns.map((col) => {
    const colKey = getColKey(col);
    if (!colKey) {
      return col;
    }
    const existingOnCell = (
      col as {
        onCell?: (
          record: DatamapReportRow,
          index?: number,
        ) => React.HTMLAttributes<HTMLElement>;
      }
    ).onCell;
    const isGroupingColumn = colKey === groupingColKey;

    return {
      ...col,
      onHeaderCell: () =>
        ({
          "data-testid": `column-${colKey}`,
        }) as React.HTMLAttributes<HTMLElement>,
      onCell: (record: DatamapReportRow, index?: number) => {
        const existing = existingOnCell?.(record, index) || {};
        const cellProps: Record<string, unknown> = {
          ...existing,
          "data-testid": `row-${index ?? 0}-col-${colKey}`,
        };

        // Apply rowSpan merging on the grouping column
        if (isGroupingColumn) {
          if (record.groupRowHidden) {
            cellProps.rowSpan = 0;
          } else if (record.groupRowSpan) {
            cellProps.rowSpan = record.groupRowSpan;
            cellProps.style = { verticalAlign: "top" };
          }
        }

        return cellProps as React.HTMLAttributes<HTMLElement>;
      },
    };
  });
};
