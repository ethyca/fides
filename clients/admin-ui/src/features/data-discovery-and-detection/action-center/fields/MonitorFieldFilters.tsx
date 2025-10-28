import { AntTreeDataNode as DataNode, Filter } from "fidesui";
import { useEffect, useMemo, useState } from "react";

import { capitalize } from "~/features/common/utils";
import { useGetDatastoreFiltersQuery } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { TaxonomyTypeEnum } from "~/features/taxonomy/constants";
import { transformTaxonomyEntityToNodes } from "~/features/taxonomy/helpers";
import { useLazyGetTaxonomyQuery } from "~/features/taxonomy/taxonomy.slice";
import { DiffStatus } from "~/types/api";

import {
  DIFF_TO_RESOURCE_STATUS,
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
        const isLeaf = index === parts.length - 1;

        nodeMap.set(key, {
          title: taxonomyInfo?.title || capitalize(key.split(".").pop() || key),
          key,
          checkable: true,
          selectable: false,
          isLeaf,
        });
      }
    });
  });

  // Build hierarchical structure by organizing parent-child relationships
  const allNodes = Array.from(nodeMap.values());

  // Helper to recursively build children for a node
  const buildChildren = (parentKey: string): DataNode[] => {
    return allNodes
      .filter((n) => {
        const nKey = n.key as string;
        const nParts = nKey.split(".");
        const parentParts = parentKey.split(".");
        // Check if this node is a direct child (one level deeper)
        return (
          nParts.length === parentParts.length + 1 &&
          nKey.startsWith(`${parentKey}.`)
        );
      })
      .map((child) => {
        const childKey = child.key as string;
        const grandchildren = buildChildren(childKey);
        return {
          ...child,
          children: grandchildren.length > 0 ? grandchildren : undefined,
          isLeaf: grandchildren.length === 0,
        };
      });
  };

  // Get root level nodes (no parent)
  const rootNodes: DataNode[] = allNodes
    .filter((node) => {
      const keyStr = node.key as string;
      const parts = keyStr.split(".");
      return parts.length === 1;
    })
    .map((node) => {
      const nodeKey = node.key as string;
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
}: ReturnType<typeof useMonitorFieldsFilters> & { monitorId: string }) => {
  // Local state for filter changes (not applied until "Apply" is clicked)
  const [localResourceStatus, setLocalResourceStatus] = useState<
    ResourceStatusLabel[] | null
  >(resourceStatus);
  const [localDataCategory, setLocalDataCategory] = useState<string[] | null>(
    dataCategory,
  );

  // Initialize with status section expanded by default
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([
    "status-section",
  ]);

  // Sync local state when external state changes
  useEffect(() => {
    setLocalResourceStatus(resourceStatus);
  }, [resourceStatus]);

  useEffect(() => {
    setLocalDataCategory(dataCategory);
  }, [dataCategory]);

  const { data: datastoreFilterResponse } = useGetDatastoreFiltersQuery(
    {
      monitor_config_id: monitorId,
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

  const availableResourceFilters = datastoreFilterResponse?.diff_status?.reduce(
    (agg, current) => {
      const diffStatus = Object.values(DiffStatus).find((rs) => rs === current);
      const currentResourceStatus = diffStatus
        ? DIFF_TO_RESOURCE_STATUS[diffStatus]
        : null;

      if (currentResourceStatus && !agg.includes(currentResourceStatus)) {
        return [...agg, currentResourceStatus];
      }

      return agg;
    },
    [] as ResourceStatusLabel[],
  );

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

  // Filter resourceStatus to only include statuses that are in available filters
  useEffect(() => {
    if (resourceStatus && availableResourceFilters) {
      const filteredStatuses = availableResourceFilters.filter(
        (status) => status !== "Confirmed" && status !== "Ignored",
      );

      // Filter resourceStatus to only include statuses that are in filteredStatuses
      const validStatuses = resourceStatus.filter((status) =>
        filteredStatuses.includes(status),
      );

      // Only update if there's a difference
      if (validStatuses.length !== resourceStatus.length) {
        setResourceStatus(validStatuses.length > 0 ? validStatuses : null);
      }
    }
  }, [availableResourceFilters, resourceStatus, setResourceStatus]);

  // Build tree data for filters
  const statusTreeData: DataNode[] = useMemo(() => {
    // Filter out "Confirmed" and "Ignored" from available filters
    const filteredStatuses =
      availableResourceFilters?.filter(
        (status) => status !== "Confirmed" && status !== "Ignored",
      ) || [];

    return filteredStatuses.map((label) => ({
      title: label,
      key: label,
      checkable: true,
      selectable: false,
      isLeaf: true,
    }));
  }, [availableResourceFilters]);

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
        key: "status-section",
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
        key: "confidence-section",
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
        key: "data-category-section",
        checkable: true,
        selectable: false,
        isLeaf: false,
        children: dataCategoryTreeData,
      });
    }

    return sections;
  }, [statusTreeData, dataCategoryTreeData]);

  // Get current checked keys from LOCAL state
  const checkedKeys = useMemo(() => {
    const keys: React.Key[] = [];
    if (localResourceStatus) {
      keys.push(...localResourceStatus);
    }
    if (localDataCategory) {
      keys.push(...localDataCategory);
    }
    return keys;
  }, [localResourceStatus, localDataCategory]);

  // Calculate active filters count from APPLIED state (not local)
  const activeFiltersCount = useMemo(() => {
    let count = 0;
    if (resourceStatus) {
      count += resourceStatus.length;
    }
    if (dataCategory) {
      count += dataCategory.length;
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
    const sectionKeys = [
      "status-section",
      "data-category-section",
      "confidence-section",
    ];

    checkedKeysArray.forEach((key) => {
      const keyStr = key.toString();

      // Skip section keys
      if (sectionKeys.includes(keyStr)) {
        return;
      }

      // Check if it's a status key
      if (availableResourceFilters?.includes(keyStr as ResourceStatusLabel)) {
        statusKeys.push(keyStr as ResourceStatusLabel);
      } else {
        // It's a data category key
        categoryKeys.push(keyStr);
      }
    });

    // Update LOCAL state only (not applied until "Apply" is clicked)
    setLocalResourceStatus(statusKeys.length > 0 ? statusKeys : null);
    setLocalDataCategory(categoryKeys.length > 0 ? categoryKeys : null);
  };

  const handleReset = () => {
    // Reset to initial state (preselect statuses except Confirmed and Ignored)
    resetToInitialState();
    // Also reset local state
    const defaultStatuses =
      availableResourceFilters?.filter(
        (status) => status !== "Confirmed" && status !== "Ignored",
      ) || [];
    setLocalResourceStatus(defaultStatuses.length > 0 ? defaultStatuses : null);
    setLocalDataCategory(null);
  };

  const handleClear = () => {
    // Clear local state immediately
    setLocalResourceStatus(null);
    setLocalDataCategory(null);
  };

  const handleApply = () => {
    // Apply the local state to the actual filter state
    setResourceStatus(localResourceStatus);
    setDataCategory(localDataCategory);
  };

  const handleExpand = (keys: React.Key[]) => {
    setExpandedKeys(keys);
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
      activeFiltersCount={activeFiltersCount}
    />
  );
};
