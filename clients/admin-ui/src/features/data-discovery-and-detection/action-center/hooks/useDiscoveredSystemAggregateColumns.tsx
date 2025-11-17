import { AntColumnsType as ColumnsType } from "fidesui";
import { useMemo, useState } from "react";

import {
  ConsentAlertInfo,
  StagedResourceTypeValue,
  SystemStagedResourcesAggregateRecord,
} from "~/types/api";

import {
  buildEditableColumns,
  buildReadOnlyColumns,
  ColumnBuilderParams,
  isIdentityProvider,
  isIdentityProviderColumns,
} from "../utils/columnBuilders";
import { ActionCenterTabHash } from "./useActionCenterTabs";

interface UseDiscoveredSystemAggregateColumnsProps {
  monitorId: string;
  readonly: boolean;
  allowIgnore?: boolean;
  onTabChange: (tab: ActionCenterTabHash) => Promise<void>;
  consentStatus?: ConsentAlertInfo;
  rowClickUrl?: (record: SystemStagedResourcesAggregateRecord) => string;
  resourceType?: StagedResourceTypeValue;
}

export const useDiscoveredSystemAggregateColumns = ({
  monitorId,
  readonly,
  allowIgnore,
  onTabChange,
  consentStatus,
  rowClickUrl,
  resourceType,
}: UseDiscoveredSystemAggregateColumnsProps) => {
  const [isLocationsExpanded, setIsLocationsExpanded] = useState(false);
  const [isDomainsExpanded, setIsDomainsExpanded] = useState(false);
  const [isDataUsesExpanded, setIsDataUsesExpanded] = useState(false);
  const [locationsVersion, setLocationsVersion] = useState(0);
  const [domainsVersion, setDomainsVersion] = useState(0);
  const [dataUsesVersion, setDataUsesVersion] = useState(0);

  const columns: ColumnsType<SystemStagedResourcesAggregateRecord> =
    useMemo(() => {
      if (isIdentityProvider(resourceType)) {
        return isIdentityProviderColumns({ rowClickUrl });
      }

      const columnBuilderParams: ColumnBuilderParams = {
        monitorId,
        readonly,
        allowIgnore,
        onTabChange,
        consentStatus,
        rowClickUrl,
        isDataUsesExpanded,
        isLocationsExpanded,
        isDomainsExpanded,
        dataUsesVersion,
        locationsVersion,
        domainsVersion,
        setIsDataUsesExpanded,
        setIsLocationsExpanded,
        setIsDomainsExpanded,
        setDataUsesVersion,
        setLocationsVersion,
        setDomainsVersion,
      };

      if (readonly) {
        return buildReadOnlyColumns(columnBuilderParams);
      }

      return buildEditableColumns(columnBuilderParams);
    }, [
      readonly,
      consentStatus,
      rowClickUrl,
      isDataUsesExpanded,
      isLocationsExpanded,
      isDomainsExpanded,
      dataUsesVersion,
      locationsVersion,
      domainsVersion,
      monitorId,
      allowIgnore,
      onTabChange,
      resourceType,
    ]);

  return { columns };
};
