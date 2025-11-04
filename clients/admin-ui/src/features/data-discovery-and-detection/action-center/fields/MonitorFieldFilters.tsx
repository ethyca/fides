import { AntTreeDataNode as DataNode, Filter } from "fidesui";
import _ from "lodash";
import { useEffect, useMemo, useState } from "react";

import { capitalize } from "~/features/common/utils";
import { useGetDatastoreFiltersQuery } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { TaxonomyTypeEnum } from "~/features/taxonomy/constants";
import { transformTaxonomyEntityToNodes } from "~/features/taxonomy/helpers";
import { useLazyGetTaxonomyQuery } from "~/features/taxonomy/taxonomy.slice";

import {
  FIELDS_FILTER_SECTION_KEYS,
  getFilterableStatuses,
  RESOURCE_STATUS,
  ResourceStatusLabel,
} from "./MonitorFields.const";
import { useMonitorFieldsFilters } from "./useFilters";
// import { ConfidenceScoreRange } from "~/types/api/models/ConfidenceScoreRange";
// const ConfidenceScoreRangeValues = Object.values(ConfidenceScoreRange);

/**
 * Build a nested tree structure from flat data category strings.
 * Uses the full taxonomy to get proper names and structure.
 */
const buildDataCategoryTree = (
  dataCategoryStrings: string[],
  taxonomyNodes: ReturnType<typeof transformTaxonomyEntityToNodes>,
): DataNode[] => {
  if (!dataCategoryStrings || dataCategoryStrings.length === 0) {
    return [];
  }

  // Helper to find a category's display name and children from taxonomy
  const findCategoryInTaxonomy = (
    key: string,
    nodes: typeof taxonomyNodes,
  ): { title: string; children: typeof taxonomyNodes } | null => {
    const findInNode = (
      node: (typeof nodes)[0],
    ): { title: string; children: typeof taxonomyNodes } | null => {
      if (node.value === key) {
        return {
          title: node.label || key,
          children: node.children || [],
        };
      }
      if (node.children && node.children.length > 0) {
        const found = findCategoryInTaxonomy(key, node.children);
        if (found) {
          return found;
        }
      }
      return null;
    };

    const result = nodes.reduce<ReturnType<typeof findInNode>>(
      (found, node) => found ?? findInNode(node),
      null,
    );
    return result;
  };

  // Build a map of all category nodes
  const nodeMap = new Map<string, DataNode>();

  // Create tree nodes from category strings
  dataCategoryStrings.forEach((category) => {
    const parts = category.split(".");

    parts.forEach((_, index) => {
      const key = parts.slice(0, index + 1).join(".");

      if (!nodeMap.has(key)) {
        const taxonomyInfo = findCategoryInTaxonomy(key, taxonomyNodes);

        nodeMap.set(key, {
          title: taxonomyInfo?.title || capitalize(key.split(".").pop() || key),
          key,
          checkable: true,
          selectable: false,
          // isLeaf will be determined during tree building based on actual children
        });
      }
    });
  });

  // Build hierarchical structure by organizing parent-child relationships
  const allNodes = Array.from(nodeMap.values());

  // Build a parent-child map for O(1) lookups instead of O(n) filtering
  const childrenMap = new Map<string, DataNode[]>();
  allNodes.forEach((node) => {
    const keyStr = node.key.toString();
    const parts = keyStr.split(".");

    if (parts.length > 1) {
      // This node has a parent
      const parentKey = parts.slice(0, -1).join(".");
      if (!childrenMap.has(parentKey)) {
        childrenMap.set(parentKey, []);
      }
      childrenMap.get(parentKey)!.push(node);
    }
  });

  // Helper to recursively build children for a node using the map
  const buildChildren = (parentKey: string): DataNode[] => {
    const children = childrenMap.get(parentKey) || [];

    return children.map((child) => {
      const childKey = child.key.toString();
      const grandchildren = buildChildren(childKey);
      return {
        ...child,
        children: grandchildren.length > 0 ? grandchildren : undefined,
        isLeaf: grandchildren.length === 0,
      };
    });
  };

  // Get root level nodes (no parent) - these are nodes with only one part
  const rootNodes: DataNode[] = allNodes
    .filter((node) => {
      const keyStr = node.key.toString();
      const parts = keyStr.split(".");
      return parts.length === 1;
    })
    .map((node) => {
      const nodeKey = node.key.toString();
      const children = buildChildren(nodeKey);
      return {
        ...node,
        children: children.length > 0 ? children : undefined,
        isLeaf: children.length === 0,
      };
    });

  return rootNodes;
};

export const MonitorFieldFilters = ({
  resourceStatus,
  setResourceStatus,
  dataCategory,
  setDataCategory,
  resetToInitialState,
  monitorId,
  stagedResourceUrn,
}: ReturnType<typeof useMonitorFieldsFilters> & {
  monitorId: string;
  stagedResourceUrn: string[];
}) => {
  // Local state for filter changes (not applied until "Apply" is clicked)
  const [localResourceStatus, setLocalResourceStatus] = useState<
    ResourceStatusLabel[] | null
  >(resourceStatus);
  const [localDataCategory, setLocalDataCategory] = useState<string[] | null>(
    dataCategory,
  );

  // Initialize with status section expanded by default
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([
    FIELDS_FILTER_SECTION_KEYS.STATUS,
  ]);

  // Sync local state when external state changes
  useEffect(() => {
    setLocalResourceStatus(resourceStatus);
  }, [resourceStatus]);

  useEffect(() => {
    setLocalDataCategory(dataCategory);
  }, [dataCategory]);

  // Reset filters to default state when stagedResourceUrn changes
  // Use JSON.stringify to compare array contents, not reference
  const stagedResourceUrnKey = stagedResourceUrn.join(",");
  useEffect(() => {
    resetToInitialState();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stagedResourceUrnKey]);

  const { data: datastoreFilterResponse, refetch: refetchDatastoreFilters } =
    useGetDatastoreFiltersQuery(
      {
        monitor_config_id: monitorId,
        staged_resource_urn: stagedResourceUrn,
      },
      { refetchOnMountOrArgChange: true },
    );

  // Fetch full taxonomy for data categories to build nested tree
  const [triggerTaxonomyQuery, { data: dataCategoriesTaxonomy = [] }] =
    useLazyGetTaxonomyQuery();

  useEffect(() => {
    triggerTaxonomyQuery(TaxonomyTypeEnum.DATA_CATEGORY);
  }, [triggerTaxonomyQuery]);

  // Transform taxonomy to tree nodes
  const taxonomyNodes = useMemo(
    () => transformTaxonomyEntityToNodes(dataCategoriesTaxonomy),
    [dataCategoriesTaxonomy],
  );

  // All statuses are always available (hardcoded)
  // const availableResourceFilters = useMemo(() => [...RESOURCE_STATUS], []);

  /* TODO: Uncomment this when we have a proper confidence score from the backend */
  /* const availableConfidenceScores =
    datastoreFilterResponse?.confidence_score?.reduce(
      (agg, current) => {
        const currentConfidenceScore = Object.values(ConfidenceScoreRange).find(
          (rs) => rs === current,
        );

        if (currentConfidenceScore) {
          return [...agg, currentConfidenceScore];
        }

        return agg;
      },
      [] as typeof ConfidenceScoreRangeValues,
    ); */

  // Build tree data for filters
  const statusTreeData: DataNode[] = useMemo(
    () =>
      RESOURCE_STATUS.map((label) => ({
        title: label.replace(/\.{3}$/, ""), // Remove trailing ellipsis for display
        key: label,
        checkable: true,
        selectable: false,
        isLeaf: true,
      })),
    [],
  );

  const dataCategoryTreeData: DataNode[] = useMemo(() => {
    if (
      !datastoreFilterResponse?.data_category ||
      datastoreFilterResponse.data_category.length === 0
    ) {
      return [];
    }

    return buildDataCategoryTree(
      datastoreFilterResponse.data_category,
      taxonomyNodes,
    );
  }, [datastoreFilterResponse?.data_category, taxonomyNodes]);

  // Combine status and data category trees
  const treeData: DataNode[] = useMemo(() => {
    const sections: DataNode[] = [];

    if (statusTreeData.length > 0) {
      sections.push({
        title: "Status",
        key: FIELDS_FILTER_SECTION_KEYS.STATUS,
        checkable: true,
        selectable: false,
        isLeaf: false,
        children: statusTreeData,
      });
    }

    /* TODO: Uncomment this when we have a proper confidence score from the backend */
    /* if (availableConfidenceScores && availableConfidenceScores.length > 0) {
      sections.push({
        title: "Confidence",
        key: FIELDS_FILTER_SECTION_KEYS.CONFIDENCE,
        checkable: true,
        selectable: false,
        isLeaf: false,
        children: availableConfidenceScores.map((cs) => ({
          title: capitalize(cs),
          key: cs,
          checkable: true,
          selectable: false,
          isLeaf: true,
        })),
      });
    } */

    if (dataCategoryTreeData.length > 0) {
      sections.push({
        title: "Data category",
        key: FIELDS_FILTER_SECTION_KEYS.DATA_CATEGORY,
        checkable: true,
        selectable: false,
        isLeaf: false,
        children: dataCategoryTreeData,
      });
    }

    return sections;
  }, [statusTreeData, dataCategoryTreeData]);

  // Get current checked keys from LOCAL state
  const checkedKeys = useMemo(() => _.uniq([
    ...(localResourceStatus ?? []), 
    ...(localDataCategory ?? [])
  ]) 
, [localResourceStatus, localDataCategory]);

  // Calculate active filters count from APPLIED state (not local)
  const activeFiltersCount = useMemo(() => {
    let count = 0;
    if (resourceStatus) {
      // Deduplicate to get accurate count
      count += new Set(resourceStatus).size;
    }
    if (dataCategory) {
      // Deduplicate to get accurate count
      count += new Set(dataCategory).size;
    }
    return count;
  }, [resourceStatus, dataCategory]);

  const handleCheck = (
    checked: React.Key[] | { checked: React.Key[]; halfChecked: React.Key[] },
  ) => {
    const checkedKeysArray = Array.isArray(checked) ? checked : checked.checked;
    // Separate status and data category selections based on their keys
    const statusKeys: ResourceStatusLabel[] = [];
    const categoryKeys: string[] = [];

    // Section keys that should be excluded from filter values
    const sectionKeys = Object.values(FIELDS_FILTER_SECTION_KEYS);

    // Helper to check if a key is a parent of any other key in the list
    // For nested categories like "user.account.settings", we only want the leaf nodes
    const isParentKey = (key: string, allKeys: string[]): boolean => {
      return allKeys.some(
        (otherKey) => otherKey !== key && otherKey.startsWith(`${key}.`),
      );
    };

    const allKeysAsStrings = checkedKeysArray.map((k) => k.toString());

    checkedKeysArray.forEach((key) => {
      const keyStr = key.toString();

      // Skip section keys
      if (sectionKeys.some((sk) => sk === keyStr)) {
        return;
      }

      const statusKey = RESOURCE_STATUS.find((rs) => rs === keyStr)
      if (statusKey) {
        statusKeys.push(statusKey);
      } else if (!isParentKey(keyStr, allKeysAsStrings)) {
        // Only include leaf data category keys (not parents)
        categoryKeys.push(keyStr);
      }
    });

    // Update LOCAL state only (not applied until "Apply" is clicked)
    // Use empty array for "no filters" instead of null
    setLocalResourceStatus(statusKeys.length > 0 ? statusKeys : []);
    setLocalDataCategory(categoryKeys.length > 0 ? categoryKeys : []);
  };

  const handleReset = () => {
    // Reset to initial state (preselect statuses except excluded ones)
    resetToInitialState();
    setLocalResourceStatus(getFilterableStatuses([...RESOURCE_STATUS]));
    setLocalDataCategory([]);
  };

  const handleClear = () => {
    // Clear local state immediately - use empty array for "no filters"
    setLocalResourceStatus([]);
    setLocalDataCategory([]);
  };

  const handleApply = () => {
    // Apply the local state to the actual filter state (deduplicated)
    setResourceStatus(
      localResourceStatus && localResourceStatus.length > 0
        ? Array.from(new Set(localResourceStatus))
        : localResourceStatus,
    );
    setDataCategory(
      localDataCategory && localDataCategory.length > 0
        ? Array.from(new Set(localDataCategory))
        : localDataCategory,
    );
  };

  const handleExpand = (keys: React.Key[]) => {
    setExpandedKeys(keys);
  };

  const handleOpenChange = (open: boolean) => {
    if (open) {
      // When popover opens, refetch data categories to ensure they're up-to-date
      refetchDatastoreFilters();
      return;
    }

    // When popover closes without applying, reset local state to match applied state
    setLocalResourceStatus(resourceStatus);
    setLocalDataCategory(dataCategory);
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
