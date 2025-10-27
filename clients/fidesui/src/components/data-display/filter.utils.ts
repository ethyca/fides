import type { TreeProps } from "antd/lib";
import { Key } from "react";

/**
 * Filters tree data based on a search term, returning only nodes that match
 * or have matching descendants. Performs a case-insensitive search on node titles.
 *
 * @param searchTerm - The search string to filter by
 * @param data - The tree data to filter
 * @returns Filtered tree data containing only matching nodes and their ancestors/descendants
 *
 * @example
 * ```ts
 * const filtered = filterTreeData("user", treeData);
 * // Returns only nodes with "user" in the title, including their parent and child nodes
 * ```
 */
export const filterTreeData = (
  searchTerm: string,
  data: TreeProps["treeData"] = [],
): TreeProps["treeData"] => {
  if (!searchTerm) {
    return data;
  }

  const lowerSearchTerm = searchTerm.toLowerCase();

  return data.reduce(
    (acc, node) => {
      const title = node.title?.toString() ?? "";
      const matchesSearch = title.toLowerCase().includes(lowerSearchTerm);
      const filteredChildren = node.children
        ? filterTreeData(searchTerm, node.children)
        : undefined;

      if (matchesSearch || (filteredChildren && filteredChildren.length > 0)) {
        acc.push({
          ...node,
          children:
            filteredChildren && filteredChildren.length > 0
              ? filteredChildren
              : node.children,
        });
      }

      return acc;
    },
    [] as NonNullable<TreeProps["treeData"]>,
  );
};

/**
 * Recursively extracts all keys from tree data structure.
 * Useful for expanding all nodes or tracking all available keys.
 *
 * @param data - The tree data to extract keys from
 * @returns Array of all keys found in the tree
 *
 * @example
 * ```ts
 * const allKeys = getAllTreeKeys(treeData);
 * // Use for expanding all nodes when searching
 * setExpandedKeys(allKeys);
 * ```
 */
export const getAllTreeKeys = (data: TreeProps["treeData"] = []): Key[] => {
  const keys: Key[] = [];
  const traverse = (nodes: NonNullable<TreeProps["treeData"]>) => {
    nodes.forEach((node) => {
      if (node.key) {
        keys.push(node.key);
      }
      if (node.children) {
        traverse(node.children);
      }
    });
  };
  traverse(data);
  return keys;
};
