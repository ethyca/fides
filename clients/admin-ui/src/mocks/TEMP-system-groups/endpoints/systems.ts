import { useEffect, useState } from "react";

import { DEFAULT_SYSTEMS_WITH_GROUPS } from "~/mocks/TEMP-system-groups/endpoints/systems-with-groups-response";
import { PaginationQueryParams } from "~/types/query-params";

import {
  CustomTaxonomyColor,
  SystemBulkAddToGroupPayload,
  SystemGroup,
  SystemUpsertWithGroups,
} from "../types";

export const DEFAULT_SYSTEM_GROUPS: SystemGroup[] = [
  {
    fides_key: "system.product_eng",
    name: "Product & ENG",
    color: CustomTaxonomyColor.YELLOW,
  },
  {
    fides_key: "system.infrastructure",
    name: "Infrastructure",
    color: CustomTaxonomyColor.BLUE,
  },
  {
    fides_key: "system.security",
    name: "Security",
    color: CustomTaxonomyColor.MINOS,
  },
  {
    fides_key: "system.HR",
    name: "HR",
    color: CustomTaxonomyColor.GREEN,
  },
  {
    fides_key: "system.marketing_analytics",
    name: "Marketing & Analytics",
    color: CustomTaxonomyColor.ORANGE,
  },
  {
    fides_key: "system.sales",
    name: "Sales",
    color: CustomTaxonomyColor.SANDSTONE,
  },
  {
    fides_key: "system.other",
    name: "Other",
    color: CustomTaxonomyColor.RED,
  },
  {
    fides_key: "system.other_but_white",
    name: "Other but white",
    color: CustomTaxonomyColor.WHITE,
  },
  {
    fides_key: "system.other_but_purple",
    name: "Other but purple",
    color: CustomTaxonomyColor.PURPLE,
  },
];

export const DEFAULT_SYSTEM_GROUPS_MAP: Record<string, SystemGroup> =
  DEFAULT_SYSTEM_GROUPS.reduce(
    (acc, group) => ({
      ...acc,
      [group.fides_key]: group,
    }),
    {} as Record<string, SystemGroup>,
  );

export const useMockGetSystemsWithGroupsQuery = ({
  page,
  size,
  search,
  groupFilters,
}: PaginationQueryParams & {
  search?: string;
  groupFilters?: string[];
}) => {
  const [isLoading, setIsLoading] = useState(false);
  useEffect(() => {
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
    }, 200);
  }, []);

  if (isLoading) {
    return {
      data: undefined,
      isLoading,
    };
  }
  return {
    data: DEFAULT_SYSTEMS_WITH_GROUPS.items.filter((s) => {
      if (search) {
        return s.name?.toLowerCase().includes(search.toLowerCase());
      }
      if (groupFilters?.length) {
        return s.groups.some((g) => groupFilters.includes(g));
      }
      return true;
    }),
    isLoading,
  };
};

export const useMockUpdateSystemWithGroupsMutation = () => {
  const update = async (system: SystemUpsertWithGroups) => {
    // eslint-disable-next-line no-promise-executor-return
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return {
      data: system,
    };
  };

  return [update];
};

export const useMockUpdateSystemWithGroupsError = () => {
  const update = async (system: SystemUpsertWithGroups) => {
    // eslint-disable-next-line no-promise-executor-return
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return {
      isError: true,
      error: {
        status: 422,
        data: {
          detail: "You picked bad groups, do better next time",
        },
      },
    };
  };

  return [update];
};

export const useMockBulkUpdateSystemWithGroupsMutation = () => {
  const bulkUpdate = async (payload: SystemBulkAddToGroupPayload) => {
    // eslint-disable-next-line no-promise-executor-return
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return {
      data: payload,
    };
  };

  return [bulkUpdate];
};
