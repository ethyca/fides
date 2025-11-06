// import { TreeDataNode } from "fidesui";
import { Key } from "react";

// import { AsyncTreeNode } from "./types";

export type ReactDataNode<T> = T & {
  key: Key;
  children?: ReactDataNode<T>[];
};

// const recBuildTree = (
//   node: AsyncTreeNode,
//   nodes: AsyncTreeNode[],
// ): TreeDataNode => ({
//   ...node,
//   children: [
//     ...nodes?.flatMap((child) =>
//       child.parent === node.key ? [recBuildTree(child, nodes)] : [],
//     ),
//     ...(node.total > node?.page * node.size
//       ? [
//           {
//             key: `SHOW_MORE__${node.key}`,
//             // title: () => (
//             //   <AsyncTreeDataLink
//             //     node={{ ...node, title: loadMoreText }}
//             //     buttonProps={{ onClick: () => _loadData(node.key) }}
//             //   />
//             // ),
//             icon: () => null,
//             isLeaf: true,
//           },
//         ]
//       : []),
//   ],
// });
