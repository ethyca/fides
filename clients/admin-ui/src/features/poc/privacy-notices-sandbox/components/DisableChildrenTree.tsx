import type { Key } from "antd/es/table/interface";
import { AntTree as Tree } from "fidesui";
import { useCallback, useMemo, useState } from "react";

import {
  INITIAL_EXPANDED_KEYS,
  PARENT_KEY,
  PARENT_KEY_WITH_UUID,
  TREE_NODES,
} from "../constants";
import type { CheckedKeysType, TreeDataNode } from "../types";

const DisableChildrenTree = ({
  checkedKeys,
  onCheckedKeysChange,
  cascadeConsent,
}: {
  checkedKeys: CheckedKeysType;
  onCheckedKeysChange: (checkedKeys: CheckedKeysType) => void;
  cascadeConsent?: boolean;
}) => {
  // State
  const [expandedKeys, setExpandedKeys] = useState<Key[]>(
    INITIAL_EXPANDED_KEYS,
  );
  const [autoExpandParent, setAutoExpandParent] = useState(true);

  // Helper functions
  const getCheckedArray = useCallback((keys: CheckedKeysType): Key[] => {
    return Array.isArray(keys) ? keys : keys.checked || [];
  }, []);

  const isParentChecked = useCallback(
    (keys: CheckedKeysType): boolean =>
      getCheckedArray(keys).includes(PARENT_KEY_WITH_UUID),
    [getCheckedArray],
  );

  const childrenDisabled = !isParentChecked(checkedKeys);

  // Event handlers
  const handleExpand = useCallback((expandedKeysValue: Key[]) => {
    setExpandedKeys(expandedKeysValue);
    setAutoExpandParent(false);
  }, []);

  const handleCheck = useCallback(
    (checkedKeysValue: CheckedKeysType) => {
      const currentCheckedArray = getCheckedArray(checkedKeysValue);
      const previousCheckedArray = getCheckedArray(checkedKeys);

      // Check if parent state changed
      const parentWasChecked =
        previousCheckedArray.includes(PARENT_KEY_WITH_UUID);
      const parentIsChecked =
        currentCheckedArray.includes(PARENT_KEY_WITH_UUID);
      const parentChanged = parentWasChecked !== parentIsChecked;

      // If cascade is enabled and parent changed, propagate to children
      if (cascadeConsent && parentChanged) {
        const childKeys = TREE_NODES.map((node) => node.key);

        if (parentIsChecked) {
          // Parent is now checked, check all children
          const newCheckedKeys = [...currentCheckedArray, ...childKeys];
          onCheckedKeysChange(newCheckedKeys);
        } else {
          // Parent is now unchecked, uncheck all children
          const newCheckedKeys = currentCheckedArray.filter(
            (key) => !childKeys.includes(key as string),
          );
          onCheckedKeysChange(newCheckedKeys);
        }
      } else {
        // No cascade or parent didn't change, pass through as normal
        onCheckedKeysChange(checkedKeysValue);
      }
    },
    [onCheckedKeysChange, cascadeConsent, checkedKeys, getCheckedArray],
  );

  // Memoized tree data
  const treeData: TreeDataNode[] = useMemo(
    () => [
      {
        title: PARENT_KEY,
        key: PARENT_KEY_WITH_UUID,
        children: TREE_NODES.map((node) => ({
          title: node.title,
          key: node.key,
          disabled: childrenDisabled,
        })),
      },
    ],
    [childrenDisabled],
  );

  return (
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
  );
};

export default DisableChildrenTree;
