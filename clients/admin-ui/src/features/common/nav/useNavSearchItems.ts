import { useMemo } from "react";

import { useGetAllDatastoreConnectionsQuery } from "~/features/datastore-connections/datastore-connection.slice";
import { useGetSystemsQuery } from "~/features/system/system.slice";
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

/** Minimum characters before server-side search fires. */
const MIN_SEARCH_LENGTH = 2;

/** Max results to fetch per dynamic source. */
const SEARCH_PAGE_SIZE = 10;

export interface FlatNavItem {
  title: string;
  path: string;
  groupTitle: string;
  parentTitle?: string;
}

/**
 * Builds the full list of searchable nav items, including:
 * - Static pages and their tabs (from nav groups, always available)
 * - Taxonomy type names (core + custom from API, always available)
 * - Dynamic system names (server-side search, fires after 2+ characters)
 * - Dynamic integration names (server-side search, fires after 2+ characters)
 */
const useNavSearchItems = (
  groups: NavGroup[],
  searchQuery: string,
): FlatNavItem[] => {
  const trimmedQuery = searchQuery.trim();
  const shouldSearch = trimmedQuery.length >= MIN_SEARCH_LENGTH;

  // Static items from nav config (always available)
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

  // Taxonomy types (small fixed set, always available)
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

  // Systems - server-side search, skipped until user types 2+ chars
  const { data: systemsData } = useGetSystemsQuery(
    { search: trimmedQuery, page: 1, size: SEARCH_PAGE_SIZE },
    { skip: !shouldSearch },
  );

  const systemItems: FlatNavItem[] = useMemo(() => {
    if (!systemsData?.items) {
      return [];
    }
    const systemGroup = groups.find((g) =>
      g.children.some((c) => c.path === "/systems"),
    );
    const groupTitle = systemGroup?.title ?? "Data inventory";

    return systemsData.items.map((sys) => ({
      title: sys.name || sys.fides_key,
      path: `/systems/configure/${sys.fides_key}`,
      groupTitle,
      parentTitle: "System inventory",
    }));
  }, [systemsData, groups]);

  // Integrations - server-side search, skipped until user types 2+ chars
  const { data: connectionsData } = useGetAllDatastoreConnectionsQuery(
    { search: trimmedQuery, page: 1, size: SEARCH_PAGE_SIZE },
    { skip: !shouldSearch },
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

  return useMemo(
    () => [
      ...staticItems,
      ...taxonomyItems,
      ...systemItems,
      ...integrationItems,
    ],
    [staticItems, taxonomyItems, systemItems, integrationItems],
  );
};

export default useNavSearchItems;
