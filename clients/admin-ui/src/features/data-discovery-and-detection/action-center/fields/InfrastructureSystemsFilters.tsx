import { Filter, TreeDataNode as DataNode } from "fidesui";
import { uniq } from "lodash";
import { useEffect, useMemo, useState } from "react";

import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { DiffStatus } from "~/types/api";

import { useGetIdentityProviderMonitorFiltersQuery } from "../../discovery-detection.slice";
import {
  INFRASTRUCTURE_DIFF_STATUS_LABEL,
  INFRASTRUCTURE_SYSTEM_FILTER_SECTION_KEYS,
  VENDOR_FILTER_OPTIONS,
} from "../constants";
import { useInfrastructureSystemsFilters } from "./useInfrastructureSystemsFilters";

interface InfrastructureSystemsFiltersProps
  extends ReturnType<typeof useInfrastructureSystemsFilters> {
  monitorId: string;
}

export const InfrastructureSystemsFilters = ({
  monitorId,
  statusFilters,
  setStatusFilters,
  vendorFilters,
  setVendorFilters,
  dataUsesFilters,
  setDataUsesFilters,
  reset,
}: InfrastructureSystemsFiltersProps) => {
  const { getDataUseDisplayName } = useTaxonomies();

  // Fetch available filters from API
  const { data: availableFilters } = useGetIdentityProviderMonitorFiltersQuery(
    { monitor_config_key: monitorId },
    { skip: !monitorId },
  );

  // Local state for filter changes (not applied until "Apply" is clicked)
  const [localStatusFilters, setLocalStatusFilters] = useState<string[]>(
    statusFilters ?? [],
  );
  const [localVendorFilters, setLocalVendorFilters] = useState<string[]>(
    vendorFilters ?? [],
  );
  const [localDataUsesFilters, setLocalDataUsesFilters] = useState<string[]>(
    dataUsesFilters ?? [],
  );

  // Initialize with status section expanded by default
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([
    INFRASTRUCTURE_SYSTEM_FILTER_SECTION_KEYS.STATUS,
  ]);

  // Sync local state when external state changes
  useEffect(() => {
    setLocalStatusFilters(statusFilters ?? []);
  }, [statusFilters]);

  useEffect(() => {
    setLocalVendorFilters(vendorFilters ?? []);
  }, [vendorFilters]);

  useEffect(() => {
    setLocalDataUsesFilters(dataUsesFilters ?? []);
  }, [dataUsesFilters]);

  // Build tree data for status filters from API response
  const statusTreeData: DataNode[] = useMemo(() => {
    if (!availableFilters?.diff_status) {
      return [];
    }
    return availableFilters.diff_status.map((status) => ({
      title: INFRASTRUCTURE_DIFF_STATUS_LABEL[status as DiffStatus] ?? status,
      key: status,
      checkable: true,
      selectable: false,
      isLeaf: true,
    }));
  }, [availableFilters?.diff_status]);

  // Build tree data for vendor filters (hardcoded known/unknown)
  const vendorTreeData: DataNode[] = useMemo(
    () =>
      VENDOR_FILTER_OPTIONS.map((option) => ({
        title: option.label,
        key: option.key,
        checkable: true,
        selectable: false,
        isLeaf: true,
      })),
    [],
  );

  // Build tree data for data uses from API response
  const dataUsesTreeData: DataNode[] = useMemo(() => {
    if (!availableFilters?.data_uses) {
      return [];
    }
    return availableFilters.data_uses.map((dataUse) => ({
      title: getDataUseDisplayName(dataUse),
      key: dataUse,
      checkable: true,
      selectable: false,
      isLeaf: true,
    }));
  }, [availableFilters?.data_uses, getDataUseDisplayName]);

  // Combine all filter trees
  const treeData: DataNode[] = useMemo(() => {
    const sections: DataNode[] = [];

    if (statusTreeData.length > 0) {
      sections.push({
        title: "Status",
        key: INFRASTRUCTURE_SYSTEM_FILTER_SECTION_KEYS.STATUS,
        checkable: true,
        selectable: false,
        isLeaf: false,
        children: statusTreeData,
      });
    }

    if (vendorTreeData.length > 0) {
      sections.push({
        title: "Vendor",
        key: INFRASTRUCTURE_SYSTEM_FILTER_SECTION_KEYS.VENDOR,
        checkable: true,
        selectable: false,
        isLeaf: false,
        children: vendorTreeData,
      });
    }

    if (dataUsesTreeData.length > 0) {
      sections.push({
        title: "Data use",
        key: INFRASTRUCTURE_SYSTEM_FILTER_SECTION_KEYS.DATA_USES,
        checkable: true,
        selectable: false,
        isLeaf: false,
        children: dataUsesTreeData,
      });
    }

    return sections;
  }, [statusTreeData, vendorTreeData, dataUsesTreeData]);

  // Get all valid keys for each filter type
  const validStatusKeys = useMemo(
    () => new Set<string>(availableFilters?.diff_status ?? []),
    [availableFilters?.diff_status],
  );

  const validVendorKeys = useMemo(
    () => new Set<string>(VENDOR_FILTER_OPTIONS.map((o) => o.key)),
    [],
  );

  const validDataUsesKeys = useMemo(
    () => new Set<string>(availableFilters?.data_uses ?? []),
    [availableFilters?.data_uses],
  );

  // Get current checked keys from LOCAL state
  const checkedKeys = useMemo(
    () =>
      uniq([
        ...localStatusFilters,
        ...localVendorFilters,
        ...localDataUsesFilters,
      ]),
    [localStatusFilters, localVendorFilters, localDataUsesFilters],
  );

  // Calculate active filters count from APPLIED state (not local)
  const activeFiltersCount = useMemo(() => {
    let count = 0;
    if (statusFilters) {
      count += new Set(statusFilters).size;
    }
    if (vendorFilters) {
      count += new Set(vendorFilters).size;
    }
    if (dataUsesFilters) {
      count += new Set(dataUsesFilters).size;
    }
    return count;
  }, [statusFilters, vendorFilters, dataUsesFilters]);

  // Section keys that should be excluded from filter values
  const sectionKeys = useMemo(
    () =>
      new Set<string>(Object.values(INFRASTRUCTURE_SYSTEM_FILTER_SECTION_KEYS)),
    [],
  );

  const handleCheck = (
    checked: React.Key[] | { checked: React.Key[]; halfChecked: React.Key[] },
  ) => {
    const checkedKeysArray = Array.isArray(checked) ? checked : checked.checked;

    const statusKeys: string[] = [];
    const vendorKeys: string[] = [];
    const dataUsesKeys: string[] = [];

    checkedKeysArray.forEach((key) => {
      const keyStr = key.toString();

      // Skip section keys
      if (sectionKeys.has(keyStr)) {
        return;
      }

      if (validStatusKeys.has(keyStr)) {
        statusKeys.push(keyStr);
      } else if (validVendorKeys.has(keyStr)) {
        vendorKeys.push(keyStr);
      } else if (validDataUsesKeys.has(keyStr)) {
        dataUsesKeys.push(keyStr);
      }
    });

    // Update LOCAL state only (not applied until "Apply" is clicked)
    setLocalStatusFilters(statusKeys);
    setLocalVendorFilters(vendorKeys);
    setLocalDataUsesFilters(dataUsesKeys);
  };

  const handleReset = () => {
    reset();
    setLocalStatusFilters([]);
    setLocalVendorFilters([]);
    setLocalDataUsesFilters([]);
  };

  const handleClear = () => {
    setLocalStatusFilters([]);
    setLocalVendorFilters([]);
    setLocalDataUsesFilters([]);
  };

  const handleApply = () => {
    setStatusFilters(
      localStatusFilters.length > 0
        ? Array.from(new Set(localStatusFilters))
        : [],
    );
    setVendorFilters(
      localVendorFilters.length > 0
        ? Array.from(new Set(localVendorFilters))
        : [],
    );
    setDataUsesFilters(
      localDataUsesFilters.length > 0
        ? Array.from(new Set(localDataUsesFilters))
        : [],
    );
  };

  const handleExpand = (keys: React.Key[]) => {
    setExpandedKeys(keys);
  };

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      // When popover closes without applying, reset local state to match applied state
      setLocalStatusFilters(statusFilters ?? []);
      setLocalVendorFilters(vendorFilters ?? []);
      setLocalDataUsesFilters(dataUsesFilters ?? []);
    }
  };

  return (
    <Filter
      treeProps={{
        checkable: true,
        checkedKeys,
        onCheck: handleCheck,
        treeData,
        expandedKeys,
        onExpand: handleExpand,
      }}
      onApply={handleApply}
      onReset={handleReset}
      onClear={handleClear}
      onOpenChange={handleOpenChange}
      activeFiltersCount={activeFiltersCount}
    />
  );
};
