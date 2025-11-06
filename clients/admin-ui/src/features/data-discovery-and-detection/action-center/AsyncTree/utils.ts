import { Key } from "react";

export type ReactDataNode<T> = T & {
  key: Key;
  children?: ReactDataNode<T>[]
}

export const findNodeParent = <T>(data: ReactDataNode<T>[], key: Key) => {
  return data.find((node) => {
    const { children } = node;
    return children && !!children.find((child) => child.key.toString() === key);
  });
};

const hasChild = <T>(data: ReactDataNode<T>, key: Key) => data.children?.find((node) => node.key = key)



// export const recFindNodeParent = <T>(
//   data: ReactDataNode<T>[],
//   key: Key,
// ): ReactDataNode<T> | null => {
//   data.find((node) => hasChild(node, key)) ?? data.reduceRight recFindNodeParent()
//   return data.find((node) => node.key === recFindNodeParent(node.children) {
//     if(node.children) {
//     return (
//       recFindNodeParent(current.children, key)
//     );
//   }
//   return agg;
// }
//   );
// };

