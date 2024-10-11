import { createColumnHelper } from "@tanstack/react-table";
import {
  DefaultCell,
  DefaultHeaderCell,
  GroupCountBadgeCell,
} from "common/table/v2";
import _, { isArray, map } from "lodash";
import { ReactNode } from "react";

import { BadgeCellExpandable } from "~/features/common/table/v2/cells";
import { CustomFieldDefinitionWithId, Page_DatamapReport_ } from "~/types/api";

import { DatamapReportWithCustomFields as DatamapReport } from "./datamap-report";

const columnHelper = createColumnHelper<DatamapReport>();

// eslint-disable-next-line @typescript-eslint/naming-convention
export enum COLUMN_IDS {
  SYSTEM_NAME = "system_name",
  DATA_USE = "data_use",
  DATA_CATEGORY = "data_categories",
  DATA_SUBJECT = "data_subjects",
  LEGAL_NAME = "legal_name",
  DPO = "dpo",
  LEGAL_BASIS_FOR_PROCESSING = "legal_basis_for_processing",
  ADMINISTRATING_DEPARTMENT = "administrating_department",
  COOKIE_MAX_AGE_SECONDS = "cookie_max_age_seconds",
  PRIVACY_POLICY = "privacy_policy",
  LEGAL_ADDRESS = "legal_address",
  COOKIE_REFRESH = "cookie_refresh",
  DATA_SECURITY_PRACTICES = "data_security_practices",
  DATA_SHARED_WITH_THIRD_PARTIES = "DATA_SHARED_WITH_THIRD_PARTIES",
  DATA_STEWARDS = "data_stewards",
  DECLARATION_NAME = "declaration_name",
  DESCRIPTION = "description",
  DOES_INTERNATIONAL_TRANSFERS = "does_international_transfers",
  DPA_LOCATION = "dpa_location",
  DESTINATIONS = "egress",
  EXEMPT_FROM_PRIVACY_REGULATIONS = "exempt_from_privacy_regulations",
  FEATURES = "features",
  FIDES_KEY = "fides_key",
  FLEXIBLE_LEGAL_BASIS_FOR_PROCESSING = "flexible_legal_basis_for_processing",
  IMPACT_ASSESSMENT_LOCATION = "impact_assessment_location",
  SOURCES = "ingress",
  JOINT_CONTROLLER_INFO = "joint_controller_info",
  LEGAL_BASIS_FOR_PROFILING = "legal_basis_for_profiling",
  LEGAL_BASIS_FOR_TRANSFERS = "legal_basis_for_transfers",
  LEGITIMATE_INTEREST_DISCLOSURE_URL = "legitimate_interest_disclosure_url",
  LINK_TO_PROCESSOR_CONTRACT = "link_to_processor_contract",
  PROCESSES_PERSONAL_DATA = "processes_personal_data",
  REASON_FOR_EXEMPTION = "reason_for_exemption",
  REQUIRES_DATA_PROTECTION_ASSESSMENTS = "requires_data_protection_assessments",
  RESPONSIBILITY = "responsibility",
  RETENTION_PERIOD = "retention_period",
  SHARED_CATEGORIES = "shared_categories",
  SPECIAL_CATEGORY_LEGAL_BASIS = "special_category_legal_basis",
  SYSTEM_DEPENDENCIES = "system_dependencies",
  THIRD_COUNTRY_SAFEGUARDS = "third_country_safeguards",
  THIRD_PARTIES = "third_parties",
  COOKIES = "cookies",
  USES_COOKIES = "uses_cookies",
  USES_NON_COOKIE_ACCESS = "uses_non_cookie_access",
  USES_PROFILING = "uses_profiling",
  SYSTEM_UNDECLARED_DATA_CATEGORIES = "system_undeclared_data_categories",
  DATA_USE_UNDECLARED_DATA_CATEGORIES = "data_use_undeclared_data_categories",
}

// Custom fields are prepended by `system_` or `privacy_declaration_`
const CUSTOM_FIELD_SYSTEM_PREFIX = "system_";
const CUSTOM_FIELD_DATA_USE_PREFIX = "privacy_declaration_";

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
      key.includes(_.snakeCase(cf.name)),
    );
    const keyWithoutPrefix = key.replace(/^(system_|privacy_declaration_)/, "");
    const displayText = _.upperFirst(keyWithoutPrefix.replaceAll("_", " "));
    return columnHelper.accessor((row) => row[key], {
      id: key,
      cell: (props) =>
        // Conditionally render the Group cell if we have more than one value.
        // Alternatively, could check the customField type
        Array.isArray(props.getValue()) ? (
          <GroupCountBadgeCell value={props.getValue()} ignoreZero {...props} />
        ) : (
          <DefaultCell value={props.getValue() as string} />
        ),
      header: (props) => <DefaultHeaderCell value={displayText} {...props} />,
      meta: {
        displayText,
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
}
export const getDatamapReportColumns = ({
  onSelectRow,
  getDataUseDisplayName,
  getDataCategoryDisplayName,
  getDataSubjectDisplayName,
  datamapReport,
  customFields,
}: DatamapReportColumnProps) => {
  const customFieldColumns = getCustomFieldColumns(datamapReport, customFields);
  return [
    columnHelper.accessor((row) => row.system_name, {
      enableGrouping: true,
      id: COLUMN_IDS.SYSTEM_NAME,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => <DefaultHeaderCell value="System" {...props} />,
      meta: {
        displayText: "System",
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
      header: (props) => <DefaultHeaderCell value="Data use" {...props} />,
      meta: {
        displayText: "Data use",
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
      header: (props) => (
        <DefaultHeaderCell value="Data categories" {...props} />
      ),
      meta: {
        displayText: "Data categories",
        showHeaderMenu: true,
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
            {...props}
          />
        );
      },
      header: (props) => <DefaultHeaderCell value="Data subject" {...props} />,
      meta: {
        displayText: "Data subject",
        showHeaderMenu: true,
      },
    }),
    columnHelper.accessor((row) => row.legal_name, {
      id: COLUMN_IDS.LEGAL_NAME,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => <DefaultHeaderCell value="Legal name" {...props} />,
      meta: {
        displayText: "Legal name",
      },
    }),
    columnHelper.accessor((row) => row.dpo, {
      id: COLUMN_IDS.DPO,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Data privacy officer" {...props} />
      ),
      meta: {
        displayText: "Data privacy officer",
      },
    }),
    columnHelper.accessor((row) => row.legal_basis_for_processing, {
      id: COLUMN_IDS.LEGAL_BASIS_FOR_PROCESSING,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Legal basis for processing" {...props} />
      ),
      meta: {
        displayText: "Legal basis for processing",
      },
    }),
    columnHelper.accessor((row) => row.administrating_department, {
      id: COLUMN_IDS.ADMINISTRATING_DEPARTMENT,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Administrating department" {...props} />
      ),
      meta: {
        displayText: "Administrating department",
      },
    }),
    columnHelper.accessor((row) => row.cookie_max_age_seconds, {
      id: COLUMN_IDS.COOKIE_MAX_AGE_SECONDS,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Cookie max age seconds" {...props} />
      ),
      meta: {
        displayText: "Cookie max age seconds",
      },
    }),
    columnHelper.accessor((row) => row.privacy_policy, {
      id: COLUMN_IDS.PRIVACY_POLICY,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Privacy policy" {...props} />
      ),
      meta: {
        displayText: "Privacy policy",
      },
    }),
    columnHelper.accessor((row) => row.legal_address, {
      id: COLUMN_IDS.LEGAL_ADDRESS,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => <DefaultHeaderCell value="Legal address" {...props} />,
      meta: {
        displayText: "Legal address",
      },
    }),
    columnHelper.accessor((row) => row.cookie_refresh, {
      id: COLUMN_IDS.COOKIE_REFRESH,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell
          value="Cookie refresh"
          table={props.table}
          header={props.header}
          column={props.column}
        />
      ),
      meta: {
        displayText: "Cookie refresh",
      },
    }),
    columnHelper.accessor((row) => row.data_security_practices, {
      id: COLUMN_IDS.DATA_SECURITY_PRACTICES,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Data security practices" {...props} />
      ),
      meta: {
        displayText: "Data security practices",
      },
    }),
    columnHelper.accessor((row) => row.data_shared_with_third_parties, {
      id: COLUMN_IDS.DATA_SHARED_WITH_THIRD_PARTIES,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Data shared with third parties" {...props} />
      ),
      meta: {
        displayText: "Data shared with third parties",
      },
    }),
    columnHelper.accessor((row) => row.data_stewards, {
      id: COLUMN_IDS.DATA_STEWARDS,
      cell: (props) => (
        <GroupCountBadgeCell
          suffix="data stewards"
          ignoreZero
          value={props.getValue()}
          {...props}
        />
      ),
      header: (props) => <DefaultHeaderCell value="Data stewards" {...props} />,
      meta: {
        displayText: "Data stewards",
        showHeaderMenu: true,
      },
    }),
    columnHelper.accessor((row) => row.declaration_name, {
      id: COLUMN_IDS.DECLARATION_NAME,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Declaration name" {...props} />
      ),
      meta: {
        displayText: "Declaration name",
      },
    }),
    columnHelper.accessor((row) => row.does_international_transfers, {
      id: COLUMN_IDS.DOES_INTERNATIONAL_TRANSFERS,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Does international transfers" {...props} />
      ),
      meta: {
        displayText: "Does international transfers",
      },
    }),
    columnHelper.accessor((row) => row.dpa_location, {
      id: COLUMN_IDS.DPA_LOCATION,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => <DefaultHeaderCell value="DPA Location" {...props} />,
      meta: {
        displayText: "DPA Location",
      },
    }),
    columnHelper.accessor((row) => row.egress, {
      id: COLUMN_IDS.DESTINATIONS,
      cell: (props) => (
        <GroupCountBadgeCell
          suffix="destinations"
          ignoreZero
          value={props.getValue()}
          {...props}
        />
      ),
      header: (props) => <DefaultHeaderCell value="Destinations" {...props} />,
      meta: {
        displayText: "Destinations",
        showHeaderMenu: true,
      },
    }),
    columnHelper.accessor((row) => row.exempt_from_privacy_regulations, {
      id: COLUMN_IDS.EXEMPT_FROM_PRIVACY_REGULATIONS,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Exempt from privacy regulations" {...props} />
      ),
      meta: {
        displayText: "Exempt from privacy regulations",
      },
    }),
    columnHelper.accessor((row) => row.features, {
      id: COLUMN_IDS.FEATURES,
      cell: (props) => (
        <GroupCountBadgeCell
          suffix="features"
          ignoreZero
          value={props.getValue()}
          {...props}
        />
      ),
      header: (props) => <DefaultHeaderCell value="Features" {...props} />,
      meta: {
        displayText: "Features",
        showHeaderMenu: true,
      },
    }),
    columnHelper.accessor((row) => row.fides_key, {
      id: COLUMN_IDS.FIDES_KEY,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => <DefaultHeaderCell value="Fides key" {...props} />,
      meta: {
        displayText: "Fides key",
      },
    }),
    columnHelper.accessor((row) => row.flexible_legal_basis_for_processing, {
      id: COLUMN_IDS.FLEXIBLE_LEGAL_BASIS_FOR_PROCESSING,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell
          value="Flexible legal basis for processing"
          {...props}
        />
      ),
      meta: {
        displayText: "Flexible legal basis for processing",
      },
    }),
    columnHelper.accessor((row) => row.impact_assessment_location, {
      id: COLUMN_IDS.IMPACT_ASSESSMENT_LOCATION,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Impact assessment location" {...props} />
      ),
      meta: {
        displayText: "Impact assessment location",
      },
    }),
    columnHelper.accessor((row) => row.ingress, {
      id: COLUMN_IDS.SOURCES,
      cell: (props) => (
        <GroupCountBadgeCell
          suffix="sources"
          ignoreZero
          value={props.getValue()}
          {...props}
        />
      ),
      header: (props) => <DefaultHeaderCell value="Sources" {...props} />,
      meta: {
        displayText: "Sources",
        showHeaderMenu: true,
      },
    }),
    columnHelper.accessor((row) => row.joint_controller_info, {
      id: COLUMN_IDS.JOINT_CONTROLLER_INFO,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Joint controller info" {...props} />
      ),
      meta: {
        displayText: "Joint controller info",
      },
    }),
    columnHelper.accessor((row) => row.legal_basis_for_profiling, {
      id: COLUMN_IDS.LEGAL_BASIS_FOR_PROFILING,
      cell: (props) => (
        <GroupCountBadgeCell
          suffix="profiles"
          ignoreZero
          value={props.getValue()}
          {...props}
        />
      ),
      header: (props) => (
        <DefaultHeaderCell value="Legal basis for profiling" {...props} />
      ),
      meta: {
        displayText: "Legal basis for profiling",
        showHeaderMenu: true,
      },
    }),
    columnHelper.accessor((row) => row.legal_basis_for_transfers, {
      id: COLUMN_IDS.LEGAL_BASIS_FOR_TRANSFERS,
      cell: (props) => (
        <GroupCountBadgeCell
          suffix="transfers"
          ignoreZero
          value={props.getValue()}
          {...props}
        />
      ),
      header: (props) => (
        <DefaultHeaderCell value="Legal basis for transfers" {...props} />
      ),
      meta: {
        displayText: "Legal basis for transfers",
        showHeaderMenu: true,
      },
    }),
    columnHelper.accessor((row) => row.legitimate_interest_disclosure_url, {
      id: COLUMN_IDS.LEGITIMATE_INTEREST_DISCLOSURE_URL,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell
          value="Legitimate interest disclosure url"
          {...props}
        />
      ),
      meta: {
        displayText: "Legitimate interest disclosure url",
      },
    }),
    columnHelper.accessor((row) => row.link_to_processor_contract, {
      id: COLUMN_IDS.LINK_TO_PROCESSOR_CONTRACT,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Link to processor contract" {...props} />
      ),
      meta: {
        displayText: "Link to processor contract",
      },
    }),
    columnHelper.accessor((row) => row.processes_personal_data, {
      id: COLUMN_IDS.PROCESSES_PERSONAL_DATA,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Processes personal data" {...props} />
      ),
      meta: {
        displayText: "Processes personal data",
      },
    }),
    columnHelper.accessor((row) => row.reason_for_exemption, {
      id: COLUMN_IDS.REASON_FOR_EXEMPTION,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Reason for exemption" {...props} />
      ),
      meta: {
        displayText: "Reason for exemption",
      },
    }),
    columnHelper.accessor((row) => row.requires_data_protection_assessments, {
      id: COLUMN_IDS.REQUIRES_DATA_PROTECTION_ASSESSMENTS,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell
          value="Requires data protection assessments"
          {...props}
        />
      ),
      meta: {
        displayText: "Requires data protection assessments",
      },
    }),
    columnHelper.accessor((row) => row.responsibility, {
      id: COLUMN_IDS.RESPONSIBILITY,
      cell: (props) => (
        <GroupCountBadgeCell
          suffix="responsibilities"
          ignoreZero
          value={props.getValue()}
          {...props}
        />
      ),
      header: (props) => (
        <DefaultHeaderCell value="Responsibility" {...props} />
      ),
      meta: {
        displayText: "Responsibility",
        showHeaderMenu: true,
      },
    }),
    columnHelper.accessor((row) => row.retention_period, {
      id: COLUMN_IDS.RETENTION_PERIOD,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Retention period" {...props} />
      ),
      meta: {
        displayText: "Retention period",
      },
    }),
    columnHelper.accessor((row) => row.shared_categories, {
      id: COLUMN_IDS.SHARED_CATEGORIES,
      cell: (props) => (
        <GroupCountBadgeCell
          suffix="shared categories"
          ignoreZero
          value={props.getValue()}
          {...props}
        />
      ),
      header: (props) => (
        <DefaultHeaderCell value="Shared categories" {...props} />
      ),
      meta: {
        displayText: "Shared categories",
        showHeaderMenu: true,
      },
    }),
    columnHelper.accessor((row) => row.special_category_legal_basis, {
      id: COLUMN_IDS.SPECIAL_CATEGORY_LEGAL_BASIS,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Special category legal basis" {...props} />
      ),
      meta: {
        displayText: "Special category legal basis",
      },
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
      header: (props) => (
        <DefaultHeaderCell value="System dependencies" {...props} />
      ),
      meta: {
        displayText: "System dependencies",
        showHeaderMenu: true,
      },
    }),
    columnHelper.accessor((row) => row.third_country_safeguards, {
      id: COLUMN_IDS.THIRD_COUNTRY_SAFEGUARDS,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Third country safeguards" {...props} />
      ),
      meta: {
        displayText: "Third country safeguards",
      },
    }),
    columnHelper.accessor((row) => row.third_parties, {
      id: COLUMN_IDS.THIRD_PARTIES,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => <DefaultHeaderCell value="Third parties" {...props} />,
      meta: {
        displayText: "Third parties",
      },
    }),
    columnHelper.accessor((row) => row.system_undeclared_data_categories, {
      id: COLUMN_IDS.SYSTEM_UNDECLARED_DATA_CATEGORIES,
      cell: (props) => {
        const value = props.getValue();

        return (
          <GroupCountBadgeCell
            ignoreZero
            suffix="system undeclared data categories"
            value={
              isArray(value)
                ? map(value, getDataCategoryDisplayName)
                : getDataCategoryDisplayName(value || "")
            }
            {...props}
          />
        );
      },
      header: (props) => (
        <DefaultHeaderCell
          value="System undeclared data categories"
          {...props}
        />
      ),
      meta: {
        displayText: "System undeclared data categories",
        showHeaderMenu: true,
      },
    }),
    columnHelper.accessor((row) => row.data_use_undeclared_data_categories, {
      id: COLUMN_IDS.DATA_USE_UNDECLARED_DATA_CATEGORIES,
      cell: (props) => {
        const value = props.getValue();

        return (
          <GroupCountBadgeCell
            ignoreZero
            suffix="data use undeclared data categories"
            value={
              isArray(value)
                ? map(value, getDataCategoryDisplayName)
                : getDataCategoryDisplayName(value || "")
            }
            {...props}
          />
        );
      },
      header: (props) => (
        <DefaultHeaderCell
          value="Data use undeclared data categories"
          {...props}
        />
      ),
      meta: {
        displayText: "Data use undeclared data categories",
        showHeaderMenu: true,
      },
    }),
    columnHelper.accessor((row) => row.cookies, {
      id: COLUMN_IDS.COOKIES,
      cell: (props) => (
        <GroupCountBadgeCell
          ignoreZero
          suffix="cookies"
          value={props.getValue()}
          {...props}
        />
      ),
      header: (props) => <DefaultHeaderCell value="Cookies" {...props} />,
      meta: {
        displayText: "Cookies",
        showHeaderMenu: true,
      },
    }),
    columnHelper.accessor((row) => row.uses_cookies, {
      id: COLUMN_IDS.USES_COOKIES,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => <DefaultHeaderCell value="Uses cookies" {...props} />,
      meta: {
        displayText: "Uses cookies",
      },
    }),
    columnHelper.accessor((row) => row.uses_non_cookie_access, {
      id: COLUMN_IDS.USES_NON_COOKIE_ACCESS,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Uses non cookie access" {...props} />
      ),
      meta: {
        displayText: "Uses non cookie access",
      },
    }),
    columnHelper.accessor((row) => row.uses_profiling, {
      id: COLUMN_IDS.USES_PROFILING,
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Uses profiling" {...props} />
      ),
      meta: {
        displayText: "Uses profiling",
      },
    }),
    // Tack on the custom field columns to the end
    ...customFieldColumns,
  ];
};
