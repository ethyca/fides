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
  cascadeAncestors?: boolean;
  onExplicitChange?: (key: Key) => void;
}

interface TreeBuildResult {
  treeData: TreeDataNode[];
  allKeys: Key[]; // All keys in the tree (for expansion)
  descendantsMap: Map<Key, Key[]>; // Fast lookup: parent key -> all descendant keys
  ancestorsMap: Map<Key, Key[]>; // Fast lookup: child key -> all ancestor keys
}

/**
 * Builds tree structure and lookup maps in a single pass through the notices
 */
const buildTreeWithMaps = (
  notices: PrivacyNoticeResponse[],
  checkedKeys: Key[],
  parentKey?: string,
  ancestorKeys: Key[] = [],
  disableChildren: boolean = false,
): TreeBuildResult => {
  const checkedArray = checkedKeys.map((k) => k.toString());

  // Initialize maps for fast lookups
  const allKeys: Key[] = []; // Collect all keys for tree expansion
  const descendantsMap = new Map<Key, Key[]>(); // Map parent key -> all descendant keys for cascade
  const ancestorsMap = new Map<Key, Key[]>(); // Map child key -> all ancestor keys
  const treeData: TreeDataNode[] = [];

  notices.forEach((notice) => {
    // Get the history ID from the first translation (if available)
    const historyId =
      notice.translations?.[0]?.privacy_notice_history_id || notice.id;

    // Determine if this node should be disabled
    // Children are only disabled if disableChildren is true AND their parent is not checked
    const disabled =
      disableChildren && parentKey ? !checkedArray.includes(parentKey) : false;

    const node: TreeDataNode = {
      title: notice.name,
      key: notice.notice_key, // Use notice_key as the tree key
      noticeHistoryId: historyId,
      noticeKey: notice.notice_key,
      disabled,
    };

    // Register this node in the lookup maps
    allKeys.push(node.key);

    // Store ancestor keys for this node
    if (ancestorKeys.length > 0) {
      ancestorsMap.set(node.key, [...ancestorKeys]);
    }

    // Recursively build children if they exist
    if (notice.children && notice.children.length > 0) {
      const {
        treeData: childTreeData,
        allKeys: childKeys,
        descendantsMap: childDescendantsMap,
        ancestorsMap: childAncestorsMap,
      } = buildTreeWithMaps(
        notice.children,
        checkedKeys,
        notice.notice_key,
        [...ancestorKeys, node.key],
        disableChildren,
      );

      // Merge child results into parent maps (bubble up from recursion)
      childKeys.forEach((key) => allKeys.push(key));
      childDescendantsMap.forEach((value, key) =>
        descendantsMap.set(key, value),
      );
      childAncestorsMap.forEach((value, key) => ancestorsMap.set(key, value));

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
    ancestorsMap,
  };
};

const PrivacyNoticesTree = ({
  privacyNotices,
  checkedKeys,
  onCheckedKeysChange,
  cascadeConsent,
  cascadeAncestors,
  onExplicitChange,
}: PrivacyNoticesTreeProps) => {
  // Build tree data and lookup maps in a single pass through the notices
  // Disable children when NOT cascading ancestors (i.e., for DESCENDANTS or NO override modes)
  const { treeData, allKeys, descendantsMap, ancestorsMap } = useMemo(
    () =>
      buildTreeWithMaps(
        privacyNotices,
        checkedKeys,
        undefined,
        [],
        !cascadeAncestors,
      ),
    [privacyNotices, checkedKeys, cascadeAncestors],
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

      let finalKeys: Key[] = newCheckedKeys;

      // Determine which key was toggled
      const toggledKey = addedKeys.length > 0 ? addedKeys[0] : removedKeys[0];
      const isChecked = addedKeys.length > 0;

      if (toggledKey !== undefined) {
        // Track the key the user explicitly clicked
        if (onExplicitChange) {
          onExplicitChange(toggledKey);
        }

        // Handle descendant cascade (parent -> children)
        if (cascadeConsent && isParentNode(toggledKey)) {
          const descendantKeys = descendantsMap.get(toggledKey) || [];
          if (isChecked) {
            // Parent was checked, check all its descendants
            finalKeys = [...new Set([...newCheckedKeys, ...descendantKeys])];
          } else {
            // Parent was unchecked, uncheck all its descendants
            finalKeys = newCheckedKeys.filter(
              (key) => !descendantKeys.includes(key),
            );
          }
        }

        // Handle ancestor cascade (child -> parents)
        if (cascadeAncestors) {
          const ancestorKeys = ancestorsMap.get(toggledKey) || [];
          if (isChecked) {
            // Child was checked, check all its ancestors
            finalKeys = [...new Set([...finalKeys, ...ancestorKeys])];
          } else {
            // Child was unchecked, uncheck all its ancestors
            finalKeys = finalKeys.filter((key) => !ancestorKeys.includes(key));
          }
        }
      }

      onCheckedKeysChange(finalKeys);
    },
    [
      cascadeConsent,
      cascadeAncestors,
      checkedKeys,
      onCheckedKeysChange,
      isParentNode,
      descendantsMap,
      ancestorsMap,
      onExplicitChange,
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
