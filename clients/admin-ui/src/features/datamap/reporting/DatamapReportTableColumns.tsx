import { ColumnDef, createColumnHelper } from "@tanstack/react-table";
import { DefaultCell, GroupCountBadgeCell } from "common/table/v2";
import { isArray, map, snakeCase } from "lodash";
import { ReactNode } from "react";

import { CustomReportColumn } from "~/features/common/custom-reports/types";
import {
  BadgeCellExpandable,
  EditableHeaderCell,
} from "~/features/common/table/v2/cells";
import { getColumnHeaderText } from "~/features/common/table/v2/util";
import { CustomFieldDefinitionWithId, Page_DatamapReport_ } from "~/types/api";

import { COLUMN_IDS, DEFAULT_COLUMN_NAMES } from "./constants";
import { DatamapReportWithCustomFields as DatamapReport } from "./datamap-report";

const columnHelper = createColumnHelper<DatamapReport>();

// Custom fields are prepended by `system_` or `privacy_declaration_`
const CUSTOM_FIELD_SYSTEM_PREFIX = "system_";
const CUSTOM_FIELD_DATA_USE_PREFIX = "privacy_declaration_";

export const getDefaultColumn: (
  columnNameMap: Record<string, CustomReportColumn | string>,
  isRenamingColumns: boolean,
) => Partial<ColumnDef<DatamapReport>> = (
  columnNameMap,
  isRenamingColumns,
) => ({
  cell: (props) => <DefaultCell value={props.getValue() as string} />,
  header: (props) => {
    const newColumnNameMap: Record<string, string> = {};
    Object.keys(columnNameMap).forEach((key) => {
      if (typeof columnNameMap[key] === "string") {
        newColumnNameMap[key] = columnNameMap[key] as string;
      } else if ((columnNameMap[key] as CustomReportColumn).label) {
        newColumnNameMap[key] =
          (columnNameMap[key] as CustomReportColumn).label || "";
      }
    });
    return (
      <EditableHeaderCell
        value={getColumnHeaderText({
          columnId: props.column.id,
          columnNameMap: newColumnNameMap,
        })}
        defaultValue={
          DEFAULT_COLUMN_NAMES[props.column.id as COLUMN_IDS] ||
          getColumnHeaderText({
            columnId: props.column.id,
          })
        }
        isEditing={isRenamingColumns}
        {...props}
      />
    );
  },
});

const getCustomFieldColumns = (
  datamapReport: Page_DatamapReport_ | undefined,
  customFields: CustomFieldDefinitionWithId[],
) => {
  // Determine custom field keys by
  // 1. If they aren't in our expected, static, columns
  // 2. If they start with one of the custom field prefixes
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

  // Create column objects for each custom field key
  const customColumns = customFieldKeys.map((key) => {
    // We need to figure out the original custom field object in order to see
    // if the value is a string[], which would want `showHeaderMenu=true`
    const customField = customFields.find((cf) =>
      key.includes(snakeCase(cf.name)),
    );
    return columnHelper.accessor((row) => row[key], {
      id: key,
      cell: (props) =>
        // Conditionally render the Group cell if we have more than one value.
        // Alternatively, could check the customField type
        Array.isArray(props.getValue()) ? (
          <GroupCountBadgeCell
            value={props.getValue()}
            ignoreZero
            badgeProps={{ variant: "outline" }}
            {...props}
          />
        ) : (
          <DefaultCell value={props.getValue() as string} />
        ),
      meta: {
        showHeaderMenu: customField?.field_type === "string[]",
      },
    });
  });

  return customColumns;
};

interface DatamapReportColumnProps {
  onSelectRow: (row: DatamapReport) => void;
  getDataUseDisplayName: (dataUseKey: string) => ReactNode;
  getDataCategoryDisplayName: (dataCategoryKey: string) => string | JSX.Element;
  getDataSubjectDisplayName: (dataSubjectKey: string) => ReactNode;
  datamapReport: Page_DatamapReport_ | undefined;
  customFields: CustomFieldDefinitionWithId[];
  isRenaming?: boolean;
}
export const getDatamapReportColumns = ({
  onSelectRow,
  getDataUseDisplayName,
  getDataCategoryDisplayName,
  getDataSubjectDisplayName,
  datamapReport,
  customFields,
  isRenaming = false,
}: DatamapReportColumnProps) => {
  const customFieldColumns = getCustomFieldColumns(datamapReport, customFields);
  return [
    columnHelper.accessor((row) => row.system_name, {
      enableGrouping: true,
      id: COLUMN_IDS.SYSTEM_NAME,
      meta: {
        onCellClick: onSelectRow,
      },
    }),
    columnHelper.accessor((row) => row.data_uses, {
      id: COLUMN_IDS.DATA_USE,
      cell: (props) => {
        const value = props.getValue();
        return (
          <GroupCountBadgeCell
            suffix="data uses"
            ignoreZero
            value={
              isArray(value)
                ? map(value, getDataUseDisplayName)
                : getDataUseDisplayName(value || "")
            }
            badgeProps={{ variant: "outline" }}
            {...props}
          />
        );
      },
      meta: {
        width: "auto",
      },
    }),
    columnHelper.accessor((row) => row.data_categories, {
      id: COLUMN_IDS.DATA_CATEGORY,
      cell: (props) => {
        const cellValues = props.getValue();
        if (!cellValues || cellValues.length === 0) {
          return null;
        }
        const values = isArray(cellValues)
          ? cellValues.map((value) => {
              return { label: getDataCategoryDisplayName(value), key: value };
            })
          : [
              {
                label: getDataCategoryDisplayName(cellValues),
                key: cellValues,
              },
            ];
        return (
          <BadgeCellExpandable
            values={values}
            cellProps={props as any}
            variant="outline"
          />
        );
      },
      meta: {
        showHeaderMenu: !isRenaming,
        showHeaderMenuWrapOption: true,
        width: "auto",
        overflow: "hidden",
      },
    }),
    columnHelper.accessor((row) => row.data_subjects, {
      id: COLUMN_IDS.DATA_SUBJECT,
      cell: (props) => {
        const value = props.getValue();

        return (
          <GroupCountBadgeCell
            suffix="data subjects"
            ignoreZero
            value={
              isArray(value)
                ? map(value, getDataSubjectDisplayName)
                : getDataSubjectDisplayName(value || "")
            }
            badgeProps={{ variant: "outline" }}
            {...props}
          />
        );
      },
      meta: {
        showHeaderMenu: !isRenaming,
      },
    }),
    columnHelper.accessor((row) => row.legal_name, {
      id: COLUMN_IDS.LEGAL_NAME,
    }),
    columnHelper.accessor((row) => row.dpo, {
      id: COLUMN_IDS.DPO,
    }),
    columnHelper.accessor((row) => row.legal_basis_for_processing, {
      id: COLUMN_IDS.LEGAL_BASIS_FOR_PROCESSING,
    }),
    columnHelper.accessor((row) => row.administrating_department, {
      id: COLUMN_IDS.ADMINISTRATING_DEPARTMENT,
    }),
    columnHelper.accessor((row) => row.cookie_max_age_seconds, {
      id: COLUMN_IDS.COOKIE_MAX_AGE_SECONDS,
    }),
    columnHelper.accessor((row) => row.privacy_policy, {
      id: COLUMN_IDS.PRIVACY_POLICY,
    }),
    columnHelper.accessor((row) => row.legal_address, {
      id: COLUMN_IDS.LEGAL_ADDRESS,
    }),
    columnHelper.accessor((row) => row.cookie_refresh, {
      id: COLUMN_IDS.COOKIE_REFRESH,
    }),
    columnHelper.accessor((row) => row.data_security_practices, {
      id: COLUMN_IDS.DATA_SECURITY_PRACTICES,
    }),
    columnHelper.accessor((row) => row.data_shared_with_third_parties, {
      id: COLUMN_IDS.DATA_SHARED_WITH_THIRD_PARTIES,
    }),
    columnHelper.accessor((row) => row.data_stewards, {
      id: COLUMN_IDS.DATA_STEWARDS,
      cell: (props) => (
        <GroupCountBadgeCell
          suffix="data stewards"
          ignoreZero
          value={props.getValue()}
          badgeProps={{ variant: "outline" }}
          {...props}
        />
      ),
      meta: {
        showHeaderMenu: !isRenaming,
        width: "auto",
      },
    }),
    columnHelper.accessor((row) => row.declaration_name, {
      id: COLUMN_IDS.DECLARATION_NAME,
    }),
    columnHelper.accessor((row) => row.does_international_transfers, {
      id: COLUMN_IDS.DOES_INTERNATIONAL_TRANSFERS,
    }),
    columnHelper.accessor((row) => row.dpa_location, {
      id: COLUMN_IDS.DPA_LOCATION,
    }),
    columnHelper.accessor((row) => row.egress, {
      id: COLUMN_IDS.DESTINATIONS,
      cell: (props) => (
        <GroupCountBadgeCell
          suffix="destinations"
          ignoreZero
          value={props.getValue()}
          badgeProps={{ variant: "outline" }}
          {...props}
        />
      ),
      meta: {
        showHeaderMenu: !isRenaming,
        width: "auto",
      },
    }),
    columnHelper.accessor((row) => row.exempt_from_privacy_regulations, {
      id: COLUMN_IDS.EXEMPT_FROM_PRIVACY_REGULATIONS,
    }),
    columnHelper.accessor((row) => row.features, {
      id: COLUMN_IDS.FEATURES,
      cell: (props) => (
        <GroupCountBadgeCell
          suffix="features"
          ignoreZero
          value={props.getValue()}
          badgeProps={{ variant: "outline" }}
          {...props}
        />
      ),
      meta: {
        showHeaderMenu: !isRenaming,
        width: "auto",
      },
    }),
    columnHelper.accessor((row) => row.fides_key, {
      id: COLUMN_IDS.FIDES_KEY,
    }),
    columnHelper.accessor((row) => row.flexible_legal_basis_for_processing, {
      id: COLUMN_IDS.FLEXIBLE_LEGAL_BASIS_FOR_PROCESSING,
    }),
    columnHelper.accessor((row) => row.impact_assessment_location, {
      id: COLUMN_IDS.IMPACT_ASSESSMENT_LOCATION,
    }),
    columnHelper.accessor((row) => row.ingress, {
      id: COLUMN_IDS.SOURCES,
      cell: (props) => (
        <GroupCountBadgeCell
          suffix="sources"
          ignoreZero
          value={props.getValue()}
          badgeProps={{ variant: "outline" }}
          {...props}
        />
      ),
      meta: {
        showHeaderMenu: !isRenaming,
        width: "auto",
      },
    }),
    columnHelper.accessor((row) => row.joint_controller_info, {
      id: COLUMN_IDS.JOINT_CONTROLLER_INFO,
    }),
    columnHelper.accessor((row) => row.legal_basis_for_profiling, {
      id: COLUMN_IDS.LEGAL_BASIS_FOR_PROFILING,
      cell: (props) => (
        <GroupCountBadgeCell
          suffix="profiles"
          ignoreZero
          value={props.getValue()}
          badgeProps={{ variant: "outline" }}
          {...props}
        />
      ),
      meta: {
        showHeaderMenu: !isRenaming,
        width: "auto",
      },
    }),
    columnHelper.accessor((row) => row.legal_basis_for_transfers, {
      id: COLUMN_IDS.LEGAL_BASIS_FOR_TRANSFERS,
      cell: (props) => (
        <GroupCountBadgeCell
          suffix="transfers"
          ignoreZero
          value={props.getValue()}
          badgeProps={{ variant: "outline" }}
          {...props}
        />
      ),
      meta: {
        showHeaderMenu: !isRenaming,
        width: "auto",
      },
    }),
    columnHelper.accessor((row) => row.legitimate_interest_disclosure_url, {
      id: COLUMN_IDS.LEGITIMATE_INTEREST_DISCLOSURE_URL,
    }),
    columnHelper.accessor((row) => row.link_to_processor_contract, {
      id: COLUMN_IDS.LINK_TO_PROCESSOR_CONTRACT,
    }),
    columnHelper.accessor((row) => row.processes_personal_data, {
      id: COLUMN_IDS.PROCESSES_PERSONAL_DATA,
    }),
    columnHelper.accessor((row) => row.reason_for_exemption, {
      id: COLUMN_IDS.REASON_FOR_EXEMPTION,
    }),
    columnHelper.accessor((row) => row.requires_data_protection_assessments, {
      id: COLUMN_IDS.REQUIRES_DATA_PROTECTION_ASSESSMENTS,
    }),
    columnHelper.accessor((row) => row.responsibility, {
      id: COLUMN_IDS.RESPONSIBILITY,
      cell: (props) => (
        <GroupCountBadgeCell
          suffix="responsibilities"
          ignoreZero
          value={props.getValue()}
          badgeProps={{ variant: "outline" }}
          {...props}
        />
      ),
      meta: {
        showHeaderMenu: !isRenaming,
        width: "auto",
      },
    }),
    columnHelper.accessor((row) => row.retention_period, {
      id: COLUMN_IDS.RETENTION_PERIOD,
    }),
    columnHelper.accessor((row) => row.shared_categories, {
      id: COLUMN_IDS.SHARED_CATEGORIES,
      cell: (props) => (
        <GroupCountBadgeCell
          suffix="shared categories"
          ignoreZero
          value={props.getValue()}
          badgeProps={{ variant: "outline" }}
          {...props}
        />
      ),
      meta: {
        showHeaderMenu: !isRenaming,
        width: "auto",
      },
    }),
    columnHelper.accessor((row) => row.special_category_legal_basis, {
      id: COLUMN_IDS.SPECIAL_CATEGORY_LEGAL_BASIS,
    }),
    columnHelper.accessor((row) => row.system_dependencies, {
      id: COLUMN_IDS.SYSTEM_DEPENDENCIES,
      cell: (props) => (
        <GroupCountBadgeCell
          suffix="dependencies"
          ignoreZero
          value={props.getValue()}
          {...props}
        />
      ),
      meta: {
        showHeaderMenu: !isRenaming,
        width: "auto",
      },
    }),
    columnHelper.accessor((row) => row.third_country_safeguards, {
      id: COLUMN_IDS.THIRD_COUNTRY_SAFEGUARDS,
    }),
    columnHelper.accessor((row) => row.third_parties, {
      id: COLUMN_IDS.THIRD_PARTIES,
    }),
    columnHelper.accessor((row) => row.system_undeclared_data_categories, {
      id: COLUMN_IDS.SYSTEM_UNDECLARED_DATA_CATEGORIES,
      cell: (props) => {
        const cellValues = props.getValue();
        if (!cellValues || cellValues.length === 0) {
          return null;
        }
        const values = isArray(cellValues)
          ? cellValues.map((value) => {
              return { label: getDataCategoryDisplayName(value), key: value };
            })
          : [
              {
                label: getDataCategoryDisplayName(cellValues),
                key: cellValues,
              },
            ];
        return (
          <BadgeCellExpandable
            values={values}
            cellProps={props as any}
            variant="outline"
          />
        );
      },
      meta: {
        showHeaderMenu: !isRenaming,
        showHeaderMenuWrapOption: true,
        width: "auto",
        overflow: "hidden",
      },
    }),
    columnHelper.accessor((row) => row.data_use_undeclared_data_categories, {
      id: COLUMN_IDS.DATA_USE_UNDECLARED_DATA_CATEGORIES,
      cell: (props) => {
        const cellValues = props.getValue();
        if (!cellValues || cellValues.length === 0) {
          return null;
        }
        const values = isArray(cellValues)
          ? cellValues.map((value) => {
              return { label: getDataCategoryDisplayName(value), key: value };
            })
          : [
              {
                label: getDataCategoryDisplayName(cellValues),
                key: cellValues,
              },
            ];
        return (
          <BadgeCellExpandable
            values={values}
            cellProps={props as any}
            variant="outline"
          />
        );
      },
      meta: {
        showHeaderMenu: !isRenaming,
        showHeaderMenuWrapOption: true,
        width: "auto",
        overflow: "hidden",
      },
    }),
    columnHelper.accessor((row) => row.cookies, {
      id: COLUMN_IDS.COOKIES,
      cell: (props) => (
        <GroupCountBadgeCell
          ignoreZero
          suffix="cookies"
          value={props.getValue()}
          badgeProps={{ variant: "outline" }}
          {...props}
        />
      ),
      meta: {
        showHeaderMenu: !isRenaming,
        width: "auto",
      },
    }),
    columnHelper.accessor((row) => row.uses_cookies, {
      id: COLUMN_IDS.USES_COOKIES,
    }),
    columnHelper.accessor((row) => row.uses_non_cookie_access, {
      id: COLUMN_IDS.USES_NON_COOKIE_ACCESS,
    }),
    columnHelper.accessor((row) => row.uses_profiling, {
      id: COLUMN_IDS.USES_PROFILING,
    }),
    // Tack on the custom field columns to the end
    ...customFieldColumns,
  ];
};
