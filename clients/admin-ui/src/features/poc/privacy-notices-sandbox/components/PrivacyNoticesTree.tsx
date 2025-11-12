import type { Key } from "antd/es/table/interface";
import { AntTree as Tree } from "fidesui";
import { useCallback, useEffect, useMemo, useState } from "react";

import type { PrivacyNoticeResponse } from "~/types/api";

export interface TreeDataNode {
  title: string;
  key: string;
  noticeKey: string;
  disabled?: boolean;
  children?: TreeDataNode[];
  noticeHistoryId?: string;
}

interface PrivacyNoticesTreeProps {
  privacyNotices: PrivacyNoticeResponse[];
  checkedKeys: Key[];
  onCheckedKeysChange: (checkedKeys: Key[]) => void;
  cascadeConsent?: boolean;
}

interface TreeBuildResult {
  treeData: TreeDataNode[];
  allKeys: Key[]; // All keys in the tree (for expansion)
  descendantsMap: Map<Key, Key[]>; // Fast lookup: parent key -> all descendant keys
}

/**
 * Builds tree structure and lookup maps in a single pass through the notices
 */
const buildTreeWithMaps = (
  notices: PrivacyNoticeResponse[],
  checkedKeys: Key[],
  parentKey?: string,
): TreeBuildResult => {
  const checkedArray = checkedKeys.map((k) => k.toString());

  // Initialize maps for fast lookups
  const allKeys: Key[] = []; // Collect all keys for tree expansion
  const descendantsMap = new Map<Key, Key[]>(); // Map parent key -> all descendant keys for cascade
  const treeData: TreeDataNode[] = [];

  notices.forEach((notice) => {
    // Get the history ID from the first translation (if available)
    const historyId =
      notice.translations?.[0]?.privacy_notice_history_id || notice.id;

    // Determine if this node should be disabled
    // Children are disabled if their parent is not checked
    const disabled = parentKey ? !checkedArray.includes(parentKey) : false;

    const node: TreeDataNode = {
      title: notice.name,
      key: notice.notice_key, // Use notice_key as the tree key
      noticeHistoryId: historyId,
      noticeKey: notice.notice_key,
      disabled,
    };

    // Register this node in the lookup maps
    allKeys.push(node.key);

    // Recursively build children if they exist
    if (notice.children && notice.children.length > 0) {
      const {
        treeData: childTreeData,
        allKeys: childKeys,
        descendantsMap: childDescendantsMap,
      } = buildTreeWithMaps(notice.children, checkedKeys, notice.notice_key);

      // Merge child results into parent maps (bubble up from recursion)
      childKeys.forEach((key) => allKeys.push(key));
      childDescendantsMap.forEach((value, key) =>
        descendantsMap.set(key, value),
      );

      // Store all descendant keys for this parent (for cascade behavior)
      descendantsMap.set(node.key, childKeys);

      // Assign child nodes
      node.children = childTreeData;
    }

    treeData.push(node);
  });

  return {
    treeData,
    allKeys,
    descendantsMap,
  };
};

const PrivacyNoticesTree = ({
  privacyNotices,
  checkedKeys,
  onCheckedKeysChange,
  cascadeConsent,
}: PrivacyNoticesTreeProps) => {
  // Build tree data and lookup maps in a single pass through the notices
  const { treeData, allKeys, descendantsMap } = useMemo(
    () => buildTreeWithMaps(privacyNotices, checkedKeys),
    [privacyNotices, checkedKeys],
  );

  const [expandedKeys, setExpandedKeys] = useState<Key[]>(allKeys);
  const [autoExpandParent, setAutoExpandParent] = useState(true);

  // Update expanded keys when tree data changes
  useEffect(() => {
    setExpandedKeys(allKeys);
  }, [allKeys]);

  // Check if a key is a parent node (has children) - O(1) lookup
  const isParentNode = useCallback(
    (key: Key): boolean => {
      const descendants = descendantsMap.get(key) || [];
      return descendants.length > 0;
    },
    [descendantsMap],
  );

  const handleExpand = useCallback((expandedKeysValue: Key[]) => {
    setExpandedKeys(expandedKeysValue);
    setAutoExpandParent(false);
  }, []);

  const handleCheck = useCallback(
    (checkedKeysValue: Key[] | { checked: Key[]; halfChecked: Key[] }) => {
      const newCheckedKeys = Array.isArray(checkedKeysValue)
        ? checkedKeysValue
        : checkedKeysValue.checked;

      // Find which keys were toggled
      const addedKeys = newCheckedKeys.filter(
        (key) => !checkedKeys.includes(key),
      );
      const removedKeys = checkedKeys.filter(
        (key) => !newCheckedKeys.includes(key),
      );

      // Determine if a parent node changed
      let parentChanged = false;
      let toggledParentKey: Key | undefined;

      if (addedKeys.length > 0) {
        [toggledParentKey] = addedKeys;
        parentChanged = isParentNode(toggledParentKey);
      } else if (removedKeys.length > 0) {
        [toggledParentKey] = removedKeys;
        parentChanged = isParentNode(toggledParentKey);
      }

      // If cascade is enabled and a parent changed, propagate to descendants
      if (cascadeConsent && parentChanged && toggledParentKey !== undefined) {
        const descendantKeys = descendantsMap.get(toggledParentKey) || [];
        const parentIsChecked = newCheckedKeys.includes(toggledParentKey);

        let finalKeys: Key[] = [];
        if (parentIsChecked) {
          // Parent was checked, check all its descendants
          finalKeys = [...new Set([...newCheckedKeys, ...descendantKeys])];
        } else {
          // Parent was unchecked, uncheck all its descendants
          finalKeys = newCheckedKeys.filter(
            (key) => !descendantKeys.includes(key),
          );
        }
        onCheckedKeysChange(finalKeys);
      } else {
        // No cascade or parent didn't change, pass through as normal
        onCheckedKeysChange(newCheckedKeys);
      }
    },
    [
      cascadeConsent,
      checkedKeys,
      onCheckedKeysChange,
      isParentNode,
      descendantsMap,
    ],
  );

  return (
    <div className="max-w-lg">
      <Tree
        checkable
        checkStrictly
        onExpand={handleExpand}
        expandedKeys={expandedKeys}
        autoExpandParent={autoExpandParent}
        onCheck={handleCheck}
        checkedKeys={checkedKeys}
        selectable={false}
        treeData={treeData}
      />
    </div>
  );
};

export default PrivacyNoticesTree;
