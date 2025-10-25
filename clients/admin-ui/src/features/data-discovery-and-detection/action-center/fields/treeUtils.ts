import { TreeResourceChangeIndicator } from "~/types/api";

import { CustomTreeDataNode } from "./types";

/**
 * Updates a node's status if it exists in the tree
 * @param list The tree or subtree to update
 * @param key The key of the node to update
 * @param status The new status to set
 * @returns The updated tree
 */
const updateNodeStatus = (
  list: CustomTreeDataNode[],
  key: React.Key,
  status: TreeResourceChangeIndicator | null | undefined,
  expandable: boolean,
): CustomTreeDataNode[] =>
  list.map((node) => {
    if (node.key === key) {
      return {
        ...node,
        status,
        // TODO: test if this works as expected
        isLeaf: !expandable,
      };
    }
    if (node.children) {
      return {
        ...node,
        children: updateNodeStatus(node.children, key, status, expandable),
      };
    }

    return node;
  });

/**
 * Helper function to remove children from a specific node in the tree
 * @param list The tree or subtree to update
 * @param key The key of the node to update
 * @returns The updated tree
 */
const removeChildrenFromNode = (
  list: CustomTreeDataNode[],
  key: React.Key,
): CustomTreeDataNode[] =>
  list.map((node) => {
    if (node.key === key) {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { children, ...nodeWithoutChildren } = node;
      return nodeWithoutChildren;
    }
    if (node.children) {
      return {
        ...node,
        children: removeChildrenFromNode(node.children, key),
      };
    }

    return node;
  });

export { removeChildrenFromNode, updateNodeStatus };
