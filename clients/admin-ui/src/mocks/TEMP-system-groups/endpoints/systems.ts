import { useEffect, useState } from "react";
import { DEFAULT_SYSTEMS_WITH_GROUPS } from "~/mocks/TEMP-system-groups/endpoints/systems-with-groups-response";
import { PaginatedResponse, PaginationQueryParams } from "~/types/query-params";
import {
  CustomTaxonomyColor,
  PaginatedSystemsWithGroups,
  SystemGroup,
  SystemResponseWithGroups,
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
];

export const DEFAULT_SYSTEM_GROUPS_MAP: Record<string, SystemGroup> =
  DEFAULT_SYSTEM_GROUPS.reduce(
    (acc, group) => {
      acc[group.fides_key] = group;
      return acc;
    },
    {} as Record<string, SystemGroup>,
  );

const usMockGetSystemsWithGroupsQuery = ({
  page,
  size,
}: PaginationQueryParams) => {
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
    data: DEFAULT_SYSTEMS_WITH_GROUPS,
    isLoading,
  };
};
