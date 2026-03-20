import { useMemo } from "react";

import {
  INITIAL_CONNECTIONS_FILTERS,
  useGetAllDatastoreConnectionsQuery,
} from "~/features/datastore-connections/datastore-connection.slice";
import { useGetAllSystemsQuery } from "~/features/system/system.slice";
import {
  CoreTaxonomiesEnum,
  TaxonomyTypeEnum,
} from "~/features/taxonomy/constants";
import { useGetCustomTaxonomiesQuery } from "~/features/taxonomy/taxonomy.slice";

import { NavGroup } from "./nav-config";

/** Core taxonomy types that are always present regardless of Plus. */
const CORE_TAXONOMY_ITEMS = [
  {
    title: CoreTaxonomiesEnum.DATA_CATEGORIES,
    key: TaxonomyTypeEnum.DATA_CATEGORY,
  },
  {
    title: CoreTaxonomiesEnum.DATA_USES,
    key: TaxonomyTypeEnum.DATA_USE,
  },
  {
    title: CoreTaxonomiesEnum.DATA_SUBJECTS,
    key: TaxonomyTypeEnum.DATA_SUBJECT,
  },
  {
    title: CoreTaxonomiesEnum.SYSTEM_GROUPS,
    key: TaxonomyTypeEnum.SYSTEM_GROUP,
  },
];

export interface FlatNavItem {
  title: string;
  path: string;
  groupTitle: string;
  parentTitle?: string;
}

/**
 * Builds the full list of searchable nav items, including:
 * - Static pages and their tabs (from nav groups)
 * - Taxonomy type names (core + custom from API)
 * - Dynamic integration items (from API)
 * - Dynamic system names (from API)
 *
 * Queries run eagerly so data is available when the user opens the search.
 */
const useNavSearchItems = (groups: NavGroup[]): FlatNavItem[] => {
  // Static items from nav config
  const staticItems: FlatNavItem[] = useMemo(() => {
    const items: FlatNavItem[] = [];
    groups.forEach((group) => {
      group.children
        .filter((child) => !child.hidden)
        .forEach((child) => {
          items.push({
            title: child.title,
            path: child.path,
            groupTitle: group.title,
          });
          child.tabs?.forEach((tab) => {
            items.push({
              title: tab.title,
              path: tab.path,
              groupTitle: group.title,
              parentTitle: child.title,
            });
          });
        });
    });
    return items;
  }, [groups]);

  // Core taxonomy types are always available

  // Custom taxonomy types from API (Plus-only, may be undefined)
  const { data: customTaxonomies } = useGetCustomTaxonomiesQuery();

  const taxonomyItems: FlatNavItem[] = useMemo(() => {
    const taxonomyGroupTitle =
      groups.find((g) => g.children.some((c) => c.path === "/taxonomy"))
        ?.title ?? "Core configuration";

    const coreKeys = new Set<string>(CORE_TAXONOMY_ITEMS.map((c) => c.key));
    const items: FlatNavItem[] = CORE_TAXONOMY_ITEMS.map((tax) => ({
      title: tax.title,
      path: `/taxonomy/${tax.key}`,
      groupTitle: taxonomyGroupTitle,
      parentTitle: "Taxonomy",
    }));

    // Append any custom taxonomy types not already covered by core
    customTaxonomies
      ?.filter((tax) => !coreKeys.has(tax.fides_key))
      .forEach((tax) => {
        items.push({
          title: tax.name || tax.fides_key,
          path: `/taxonomy/${tax.fides_key}`,
          groupTitle: taxonomyGroupTitle,
          parentTitle: "Taxonomy",
        });
      });

    return items;
  }, [customTaxonomies, groups]);

  // Integration data
  const { data: connectionsData } = useGetAllDatastoreConnectionsQuery(
    INITIAL_CONNECTIONS_FILTERS,
  );

  const integrationItems: FlatNavItem[] = useMemo(() => {
    if (!connectionsData?.items) {
      return [];
    }
    const integrationGroup = groups.find((g) =>
      g.children.some((c) => c.path === "/integrations"),
    );
    const groupTitle = integrationGroup?.title ?? "Core configuration";

    return connectionsData.items.map((conn) => ({
      title: conn.name || conn.key,
      path: `/integrations/${conn.key}`,
      groupTitle,
      parentTitle: "Integrations",
    }));
  }, [connectionsData, groups]);

  // System names from API
  const { data: systems } = useGetAllSystemsQuery();

  const systemItems: FlatNavItem[] = useMemo(() => {
    if (!systems) {
      return [];
    }
    const systemGroup = groups.find((g) =>
      g.children.some((c) => c.path === "/systems"),
    );
    const groupTitle = systemGroup?.title ?? "Data inventory";

    return systems.map((sys) => ({
      title: sys.name || sys.fides_key,
      path: `/systems/configure/${sys.fides_key}`,
      groupTitle,
      parentTitle: "System inventory",
    }));
  }, [systems, groups]);

  return useMemo(
    () => [
      ...staticItems,
      ...taxonomyItems,
      ...integrationItems,
      ...systemItems,
    ],
    [staticItems, taxonomyItems, integrationItems, systemItems],
  );
};

export default useNavSearchItems;
