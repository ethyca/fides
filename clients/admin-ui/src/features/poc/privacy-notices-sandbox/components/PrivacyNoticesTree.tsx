import type { Key } from "antd/es/table/interface";
import { Tree } from "fidesui";
import { useCallback, useEffect, useMemo, useState } from "react";

import type { PrivacyNoticeResponse } from "~/types/api";

export interface TreeDataNode {
  title: string;
  key: string;
  noticeKey: string;
  children?: TreeDataNode[];
  noticeHistoryId?: string;
}

interface PrivacyNoticesTreeProps {
  privacyNotices: PrivacyNoticeResponse[];
  checkedKeys: Key[];
  onCheckedKeysChange: (checkedKeys: Key[]) => void;
  onExplicitChange?: (key: Key) => void;
}

interface TreeBuildResult {
  treeData: TreeDataNode[];
  allKeys: Key[]; // All keys in the tree (for expansion)
}

/**
 * Builds tree structure from privacy notices
 */
const buildTree = (notices: PrivacyNoticeResponse[]): TreeBuildResult => {
  const allKeys: Key[] = [];

  const traverse = (noticeList: PrivacyNoticeResponse[]) => {
    return noticeList.map((notice) => {
      // Get the history ID from the first translation (if available)
      const historyId =
        notice.translations?.[0]?.privacy_notice_history_id || notice.id;

      const node: TreeDataNode = {
        title: notice.name,
        key: notice.notice_key, // Use notice_key as the tree key
        noticeHistoryId: historyId,
        noticeKey: notice.notice_key,
      };

      allKeys.push(node.key);

      // Recursively build children if they exist
      if (notice.children && notice.children.length > 0) {
        node.children = traverse(notice.children);
      }

      return node;
    });
  };

  return {
    treeData: traverse(notices),
    allKeys,
  };
};

const PrivacyNoticesTree = ({
  privacyNotices,
  checkedKeys,
  onCheckedKeysChange,
  onExplicitChange,
}: PrivacyNoticesTreeProps) => {
  // Build tree data from privacy notices
  const { treeData, allKeys } = useMemo(
    () => buildTree(privacyNotices),
    [privacyNotices],
  );

  const [expandedKeys, setExpandedKeys] = useState<Key[]>(allKeys);
  const [autoExpandParent, setAutoExpandParent] = useState(true);

  // Update expanded keys when tree data changes
  useEffect(() => {
    setExpandedKeys(allKeys);
  }, [allKeys]);

  const handleExpand = useCallback((expandedKeysValue: Key[]) => {
    setExpandedKeys(expandedKeysValue);
    setAutoExpandParent(false);
  }, []);

  const handleCheck = useCallback(
    (checkedKeysValue: Key[] | { checked: Key[]; halfChecked: Key[] }) => {
      const newCheckedKeys = Array.isArray(checkedKeysValue)
        ? checkedKeysValue
        : checkedKeysValue.checked;

      // Find which key was toggled
      const addedKeys = newCheckedKeys.filter(
        (key) => !checkedKeys.includes(key),
      );
      const removedKeys = checkedKeys.filter(
        (key) => !newCheckedKeys.includes(key),
      );

      const toggledKey = addedKeys.length > 0 ? addedKeys[0] : removedKeys[0];

      if (toggledKey !== undefined && onExplicitChange) {
        // Track the key the user explicitly clicked
        onExplicitChange(toggledKey);
      }

      // Simply update checked keys without any cascading
      onCheckedKeysChange(newCheckedKeys);
    },
    [checkedKeys, onCheckedKeysChange, onExplicitChange],
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
