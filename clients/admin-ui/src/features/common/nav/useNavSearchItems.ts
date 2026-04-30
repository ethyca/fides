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
  /** Hand-curated aliases/synonyms; matched by nav search alongside title/group/parent. */
  keywords?: string[];
}

/**
 * Relevance rank for a nav item against a query, lower is better:
 *   0 = title (direct) match
 *   1 = parent-page title match
 *   2 = group title match
 *   3 = keyword/alias match
 *   Number.POSITIVE_INFINITY = no match
 *
 * An empty/whitespace query ranks every item as 0 (no preference).
 */
export const navMatchRank = (item: FlatNavItem, query: string): number => {
  const q = query.trim().toLowerCase();
  if (!q) {
    return 0;
  }
  if (item.title.toLowerCase().includes(q)) {
    return 0;
  }
  if (item.parentTitle?.toLowerCase().includes(q)) {
    return 1;
  }
  if (item.groupTitle.toLowerCase().includes(q)) {
    return 2;
  }
  if (item.keywords?.some((k) => k.toLowerCase().includes(q))) {
    return 3;
  }
  return Number.POSITIVE_INFINITY;
};

/**
 * Case-insensitive substring match for a nav item. Checks the item's title,
 * group title, parent title, and any hand-curated keywords.
 * An empty/whitespace query matches everything.
 */
export const matchesNavQuery = (item: FlatNavItem, query: string): boolean =>
  Number.isFinite(navMatchRank(item, query));

/**
 * Filter `items` to those matching `query`, then sort by relevance so that
 * direct title matches appear before parent/group/keyword matches. Stable
 * within each rank, preserving the original nav-config ordering.
 */
export const filterAndRankNavItems = (
  items: FlatNavItem[],
  query: string,
): FlatNavItem[] =>
  items
    .map((item) => ({ item, rank: navMatchRank(item, query) }))
    .filter(({ rank }) => Number.isFinite(rank))
    .sort((a, b) => a.rank - b.rank)
    .map(({ item }) => item);

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
  const staticItems: FlatNavItem[] = useMemo(
    () =>
      groups.flatMap((group) =>
        group.children
          .filter((child) => !child.hidden)
          .flatMap((child) => [
            {
              title: child.title,
              path: child.path,
              groupTitle: group.title,
              keywords: child.keywords,
            },
            ...(child.tabs?.map((tab) => ({
              title: tab.title,
              path: tab.path,
              groupTitle: group.title,
              parentTitle: child.title,
              keywords: tab.keywords,
            })) ?? []),
          ]),
      ),
    [groups],
  );

  // Taxonomy types (small fixed set, always available)
  const { data: customTaxonomies } = useGetCustomTaxonomiesQuery();

  const taxonomyItems: FlatNavItem[] = useMemo(() => {
    const taxonomyGroupTitle =
      groups.find((g) => g.children.some((c) => c.path === "/taxonomy"))
        ?.title ?? "Core configuration";

    const coreKeys = new Set<string>(CORE_TAXONOMY_ITEMS.map((c) => c.key));

    return [
      ...CORE_TAXONOMY_ITEMS.map((tax) => ({
        title: tax.title,
        path: `/taxonomy/${tax.key}`,
        groupTitle: taxonomyGroupTitle,
        parentTitle: "Taxonomy",
      })),
      ...(customTaxonomies ?? [])
        .filter((tax) => !coreKeys.has(tax.fides_key))
        .map((tax) => ({
          title: tax.name || tax.fides_key,
          path: `/taxonomy/${tax.fides_key}`,
          groupTitle: taxonomyGroupTitle,
          parentTitle: "Taxonomy",
        })),
    ];
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
