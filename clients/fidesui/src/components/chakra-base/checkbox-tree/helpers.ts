import { TreeNode, TreeNodes } from "./types";

export const getAncestorsAndCurrent = (nodeName: string) => {
  const splitNames = nodeName.split(".");
  const ancestors: string[] = [];
  splitNames.forEach((name) => {
    const parent =
      ancestors.length > 0 ? ancestors[ancestors.length - 1] : null;
    if (!parent) {
      ancestors.push(name);
    } else {
      ancestors.push(`${parent}.${name}`);
    }
  });
  return ancestors;
};

export const ancestorIsSelected = (selected: string[], nodeName: string) => {
  const ancestors = getAncestorsAndCurrent(nodeName).filter(
    (a) => a !== nodeName,
  );
  const intersection = selected.filter((s) => ancestors.includes(s));
  return intersection.length > 0;
};

export const matchNodeOrDescendant = (value: string, match: string) => {
  if (value === match) {
    return true;
  }
  if (value.startsWith(`${match}.`)) {
    return true;
  }
  return false;
};

export const getDescendantsAndCurrent = (
  nodes: TreeNodes,
  nodeName: string,
): TreeNodes => {
  const descendants: TreeNode[] = [];
  nodes.forEach((node) => {
    if (node.children) {
      descendants.push(...getDescendantsAndCurrent(node.children, nodeName));
    }
    if (matchNodeOrDescendant(node.value, nodeName)) {
      descendants.push(node);
    }
  });
  return descendants;
};
