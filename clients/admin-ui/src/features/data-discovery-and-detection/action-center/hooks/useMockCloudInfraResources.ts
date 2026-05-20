import { DefaultOptionType } from "fidesui";
import { useCallback, useMemo, useState } from "react";

import { DiffStatus } from "~/types/api";
import { CloudInfraStagedResource } from "~/types/api/models/CloudInfraStagedResource";

import { MOCK_AWS_RESOURCES } from "../mock/awsCloudInfraMock";

interface ResourceOverride {
  assignedSystems: DefaultOptionType[];
  diff_status?: DiffStatus;
}

interface UseMockCloudInfraResourcesArgs {
  statusFilters?: string[] | null;
  locationFilters?: string[] | null;
  serviceFilters?: string[] | null;
  accountFilters?: string[] | null;
  search: string;
  searchRegex: boolean;
}

const matchesSearch = (
  resource: CloudInfraStagedResource,
  search: string,
  regex: boolean,
): boolean => {
  if (!search) {
    return true;
  }
  const haystacks = [resource.name ?? "", resource.source_id, resource.urn];
  if (regex) {
    try {
      const re = new RegExp(search, "i");
      return haystacks.some((h) => re.test(h));
    } catch {
      return false;
    }
  }
  const needle = search.toLowerCase();
  return haystacks.some((h) => h.toLowerCase().includes(needle));
};

const EMPTY_SYSTEMS: DefaultOptionType[] = [];

export const useMockCloudInfraResources = ({
  statusFilters,
  locationFilters,
  serviceFilters,
  accountFilters,
  search,
  searchRegex,
}: UseMockCloudInfraResourcesArgs) => {
  const [overrides, setOverrides] = useState<Record<string, ResourceOverride>>(
    {},
  );

  const merged = useMemo<CloudInfraStagedResource[]>(
    () =>
      MOCK_AWS_RESOURCES.map((r) => {
        const o = overrides[r.urn];
        if (!o) {
          return r;
        }
        return { ...r, diff_status: o.diff_status ?? r.diff_status };
      }),
    [overrides],
  );

  const filtered = useMemo(() => {
    return merged.filter((r) => {
      if (!matchesSearch(r, search, searchRegex)) {
        return false;
      }
      if (
        statusFilters?.length &&
        !statusFilters.includes(r.diff_status as DiffStatus)
      ) {
        return false;
      }
      if (locationFilters?.length && !locationFilters.includes(r.location)) {
        return false;
      }
      if (serviceFilters?.length && !serviceFilters.includes(r.service)) {
        return false;
      }
      if (
        accountFilters?.length &&
        !accountFilters.includes(r.cloud_account_id)
      ) {
        return false;
      }
      return true;
    });
  }, [
    merged,
    search,
    searchRegex,
    statusFilters,
    locationFilters,
    serviceFilters,
    accountFilters,
  ]);

  const updateOverride = useCallback(
    (urn: string, patch: Partial<ResourceOverride>) =>
      setOverrides((prev) => {
        const current = prev[urn] ?? { assignedSystems: EMPTY_SYSTEMS };
        return { ...prev, [urn]: { ...current, ...patch } };
      }),
    [],
  );

  const addSystem = useCallback(
    (urn: string, system: DefaultOptionType) =>
      setOverrides((prev) => {
        const current = prev[urn] ?? { assignedSystems: EMPTY_SYSTEMS };
        if (current.assignedSystems.some((s) => s.value === system.value)) {
          return prev;
        }
        return {
          ...prev,
          [urn]: {
            ...current,
            assignedSystems: [...current.assignedSystems, system],
          },
        };
      }),
    [],
  );

  const removeSystem = useCallback(
    (urn: string, systemValue: DefaultOptionType["value"]) =>
      setOverrides((prev) => {
        const current = prev[urn];
        if (!current) {
          return prev;
        }
        return {
          ...prev,
          [urn]: {
            ...current,
            assignedSystems: current.assignedSystems.filter(
              (s) => s.value !== systemValue,
            ),
          },
        };
      }),
    [],
  );

  const clearSystems = useCallback(
    (urn: string) => updateOverride(urn, { assignedSystems: EMPTY_SYSTEMS }),
    [updateOverride],
  );

  const approve = useCallback(
    (urn: string) => updateOverride(urn, { diff_status: DiffStatus.MONITORED }),
    [updateOverride],
  );

  const ignore = useCallback(
    (urn: string) => updateOverride(urn, { diff_status: DiffStatus.MUTED }),
    [updateOverride],
  );

  const restore = useCallback(
    (urn: string) => updateOverride(urn, { diff_status: DiffStatus.ADDITION }),
    [updateOverride],
  );

  const getAssignedSystems = useCallback(
    (urn: string): DefaultOptionType[] =>
      overrides[urn]?.assignedSystems ?? EMPTY_SYSTEMS,
    [overrides],
  );

  return {
    data: { items: filtered, total: filtered.length },
    isLoading: false,
    isFetching: false,
    getAssignedSystems,
    addSystem,
    removeSystem,
    clearSystems,
    approve,
    ignore,
    restore,
  };
};
