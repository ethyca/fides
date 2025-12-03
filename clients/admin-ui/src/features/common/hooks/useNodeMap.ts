import _ from "lodash";
import { Key, useState } from "react";

/** Note: should be adding __type and optional relational types in future iterations */
export type Node<T> = T & {
  key: Key;
};

export type NodeMap<N> = Map<Key, Node<N>>;

export const mapNodes = <Data>(data: Node<Data>[]): NodeMap<Data> =>
  new Map(data.map((d) => [d.key, d]));

const mergeNodes = <Data>(prev: NodeMap<Data>, next: NodeMap<Data>) =>
  _([...next.entries()])
    .map(([key, node]) =>
      _.chain(prev.get(key)).defaultTo(node).merge(node).value(),
    )
    .thru(mapNodes)
    .value();

const useNodeMap = <Data>(
  initialData?: NodeMap<Data>,
  partialUpdates = true,
) => {
  const [nodes, setNodeMapState] = useState<NodeMap<Data>>(
    initialData ?? new Map(),
  );

  const update = (next: NodeMap<Data>) => {
    const nextDraft = partialUpdates ? mergeNodes(nodes, next) : next;
    const hasChanges = _([...nextDraft.entries()]).some(
      ([key, node]) => !_.isEqual(nodes.get(key), node),
    );

    if (hasChanges) {
      setNodeMapState((prev) => new Map([...prev, ...nextDraft]));
    }
  };

  const reset = () => {
    setNodeMapState(new Map());
  };

  return { nodes, update, reset };
};

export default useNodeMap;
