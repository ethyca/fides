import type { Key } from "antd/es/table/interface";
import { AntTree as Tree } from "fidesui";
import { useCallback, useEffect, useMemo, useState } from "react";

import type { PrivacyNoticeResponse } from "~/types/api";

export interface TreeDataNode {
  title: string;
  key: string;
  disabled?: boolean;
  children?: TreeDataNode[];
  noticeHistoryId?: string;
  noticeKey?: string;
}

interface PrivacyNoticesTreeProps {
  privacyNotices: PrivacyNoticeResponse[];
  checkedKeys: Key[];
  onCheckedKeysChange: (checkedKeys: Key[]) => void;
  cascadeConsent?: boolean;
}

/**
 * Builds a tree structure from privacy notices with parent-child relationships
 */
const buildTreeFromNotices = (
  notices: PrivacyNoticeResponse[],
  checkedKeys: Key[],
  parentKey?: string,
): TreeDataNode[] => {
  const checkedArray = checkedKeys.map((k) => k.toString());

  return notices.map((notice) => {
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

    // Recursively build children if they exist
    if (notice.children && notice.children.length > 0) {
      node.children = buildTreeFromNotices(
        notice.children,
        checkedKeys,
        notice.notice_key,
      );
    }

    return node;
  });
};

const PrivacyNoticesTree = ({
  privacyNotices,
  checkedKeys,
  onCheckedKeysChange,
  cascadeConsent,
}: PrivacyNoticesTreeProps) => {
  // Build tree data from privacy notices
  // Tree data depends on both notices and checked keys (for disabled state)
  const treeData = useMemo(() => {
    return buildTreeFromNotices(privacyNotices, checkedKeys);
  }, [privacyNotices, checkedKeys]);

  // Get all keys for default expansion
  const allKeys = useMemo(() => {
    const keys: Key[] = [];
    const traverse = (nodes: TreeDataNode[]) => {
      nodes.forEach((node) => {
        keys.push(node.key);
        if (node.children) {
          traverse(node.children);
        }
      });
    };
    traverse(treeData);
    return keys;
  }, [treeData]);

  const [expandedKeys, setExpandedKeys] = useState<Key[]>(allKeys);
  const [autoExpandParent, setAutoExpandParent] = useState(true);

  // Update expanded keys when tree data changes
  useEffect(() => {
    setExpandedKeys(allKeys);
  }, [allKeys]);

  // Get children keys for a given parent key
  const getChildrenKeys = useCallback(
    (parentKey: Key): Key[] => {
      const children: Key[] = [];
      const findChildren = (nodes: TreeDataNode[]): boolean => {
        return nodes.some((node) => {
          if (node.key === parentKey) {
            if (node.children) {
              const traverse = (nodeList: TreeDataNode[]) => {
                nodeList.forEach((child) => {
                  children.push(child.key);
                  if (child.children) {
                    traverse(child.children);
                  }
                });
              };
              traverse(node.children);
            }
            return true;
          }
          if (node.children && findChildren(node.children)) {
            return true;
          }
          return false;
        });
      };
      findChildren(treeData);
      return children;
    },
    [treeData],
  );

  // Check if a key is a parent node (has children)
  const isParentNode = useCallback(
    (key: Key): boolean => {
      const findNode = (nodes: TreeDataNode[]): TreeDataNode | null => {
        let found: TreeDataNode | null = null;
        nodes.some((node) => {
          if (node.key === key) {
            found = node;
            return true;
          }
          if (node.children) {
            const childFound = findNode(node.children);
            if (childFound) {
              found = childFound;
              return true;
            }
          }
          return false;
        });
        return found;
      };
      const node = findNode(treeData);
      return node?.children !== undefined && node.children.length > 0;
    },
    [treeData],
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

      // If cascade is enabled and a parent changed, propagate to children
      if (cascadeConsent && parentChanged && toggledParentKey !== undefined) {
        const childrenKeys = getChildrenKeys(toggledParentKey);
        const parentIsChecked = newCheckedKeys.includes(toggledParentKey);

        if (parentIsChecked) {
          // Parent was checked, check all its children
          const finalKeys = [...newCheckedKeys, ...childrenKeys];
          onCheckedKeysChange([...new Set(finalKeys)]);
        } else {
          // Parent was unchecked, uncheck all its children
          const finalKeys = newCheckedKeys.filter(
            (key) => !childrenKeys.includes(key),
          );
          onCheckedKeysChange(finalKeys);
        }
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
      getChildrenKeys,
    ],
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

export default PrivacyNoticesTree;
