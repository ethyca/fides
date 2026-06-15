import { UNCATEGORIZED_SEGMENT } from "~/features/common/nav/routes";
import { SystemStagedResourcesAggregateRecord } from "~/types/api";

/**
 * A flat (1-level) tree node representing a system grouping in the website
 * monitor "Asset explorer". Each node maps to a row from the
 * system-aggregate-results endpoint.
 */
export interface WebsiteSystemTreeNodeData {
  key: string;
  title: string;
  isLeaf: true;
  selectable: true;
  /** The originating aggregate record, used by the tree's titleRender. */
  record: SystemStagedResourcesAggregateRecord;
  /** Locally-tracked asset count (kept in sync for optimistic feedback). */
  count: number;
}

/**
 * The node key is the value passed to the assets query as `resolved_system_id`.
 * For a real system or vendor this is `record.id`; truly uncategorized rows
 * (no system and no vendor) fall back to the shared sentinel.
 */
export const getNodeKeyForSystem = (
  record: SystemStagedResourcesAggregateRecord,
): string => record.id ?? UNCATEGORIZED_SEGMENT;

export const isUncategorizedKey = (key: string): boolean =>
  key === UNCATEGORIZED_SEGMENT;

/**
 * Transform system-aggregate-results items into flat tree nodes, with the
 * "Uncategorized" grouping forced to the top (matching the table view and the
 * backend's own ordering).
 */
export const mapAggregateToTreeNodes = (
  items: SystemStagedResourcesAggregateRecord[],
): WebsiteSystemTreeNodeData[] => {
  const nodes: WebsiteSystemTreeNodeData[] = items.map((record) => {
    const key = getNodeKeyForSystem(record);
    return {
      key,
      title: record.name ?? (isUncategorizedKey(key) ? "Uncategorized" : key),
      isLeaf: true,
      selectable: true,
      record,
      count: record.total_updates ?? 0,
    };
  });

  return [...nodes].sort((a, b) => {
    if (isUncategorizedKey(a.key)) {
      return -1;
    }
    if (isUncategorizedKey(b.key)) {
      return 1;
    }
    return 0;
  });
};

/**
 * Apply an optimistic count delta when an asset is reassigned between systems,
 * without refetching the aggregate. Returns a new node list.
 */
export const applyCountDelta = (
  nodes: WebsiteSystemTreeNodeData[],
  { fromSystemId, toSystemId }: { fromSystemId?: string; toSystemId?: string },
): WebsiteSystemTreeNodeData[] =>
  nodes.map((node) => {
    if (fromSystemId && node.key === fromSystemId) {
      return { ...node, count: Math.max(0, node.count - 1) };
    }
    if (toSystemId && node.key === toSystemId) {
      return { ...node, count: node.count + 1 };
    }
    return node;
  });
