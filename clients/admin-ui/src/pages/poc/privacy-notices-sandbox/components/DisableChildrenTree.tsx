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

export const DisableChildrenTree = ({
  checkedKeys,
  onCheckedKeysChange,
}: {
  checkedKeys: CheckedKeysType;
  onCheckedKeysChange: (checkedKeys: CheckedKeysType) => void;
}) => {
  // State
  const [expandedKeys, setExpandedKeys] = useState<Key[]>(
    INITIAL_EXPANDED_KEYS,
  );
  const [selectedKeys, setSelectedKeys] = useState<Key[]>([]);
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
      onCheckedKeysChange(checkedKeysValue);
    },
    [onCheckedKeysChange],
  );

  const handleSelect = useCallback((selectedKeysValue: Key[]) => {
    setSelectedKeys(selectedKeysValue);
  }, []);

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
      onSelect={handleSelect}
      selectedKeys={selectedKeys}
      treeData={treeData}
    />
  );
};
