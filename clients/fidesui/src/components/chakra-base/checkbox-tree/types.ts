export type TreeNodes = readonly TreeNode[];
export interface TreeNode {
  label: string;
  value: string;
  children: TreeNodes;
}
