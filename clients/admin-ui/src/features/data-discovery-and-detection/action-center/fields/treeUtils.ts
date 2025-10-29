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
): CustomTreeDataNode[] =>
  list.map((node) => {
    if (node.key === key) {
      return {
        ...node,
        status,
      };
    }
    if (node.children) {
      return {
        ...node,
        children: updateNodeStatus(node.children, key, status),
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

/**
 * Recursively collects all descendant URNs from a node
 * @param node The node to start from
 * @returns Array of all descendant URNs (including nested children)
 */
const collectAllDescendantUrns = (node: CustomTreeDataNode): string[] => {
  const descendants: string[] = [];

  if (node.children && node.children.length > 0) {
    node.children.forEach((child) => {
      if (typeof child.key === "string") {
        descendants.push(child.key);
        // Recursively collect descendants of this child
        descendants.push(...collectAllDescendantUrns(child));
      }
    });
  }

  return descendants;
};

/**
 * Finds a node in the tree by its URN
 * @param treeData The tree to search
 * @param urn The URN to find
 * @returns The node if found, undefined otherwise
 */
const findNodeByUrn = (
  treeData: CustomTreeDataNode[],
  urn: string,
): CustomTreeDataNode | undefined => {
  // Use for loop for true early termination - unlike reduce() which continues
  // iterating through all remaining elements even after finding a match,
  // for loop allows immediate exit when the target is found, improving
  // performance on large trees by avoiding unnecessary iterations
  // eslint-disable-next-line no-restricted-syntax
  for (const node of treeData) {
    if (node.key === urn) {
      return node;
    }
    if (node.children) {
      const found = findNodeByUrn(node.children, urn);
      if (found) {
        return found;
      }
    }
  }
  return undefined;
};

export {
  collectAllDescendantUrns,
  findNodeByUrn,
  removeChildrenFromNode,
  updateNodeStatus,
};
