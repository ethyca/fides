import _ from "lodash";
import { Key, useState } from "react";

/** Note: should be adding __type and optional relational types in future iterations */
export type Node<T> = T & {
  key: Key;
};

export type NodeMap<N> = Map<Key, Node<N>>;

export const mapNodes = <Data>(data: Node<Data>[]): NodeMap<Data> =>
  new Map(data.map((d) => [d.key, d]));

export const mergeNodes = <Data>(prev: NodeMap<Data>, next: NodeMap<Data>) =>
  _([...new Map([...prev, ...next]).entries()])
    .map(([key, node]) =>
      _.chain(prev.get(key))
        .defaultTo(node)
        .cloneDeep() /** This is needed since we aren't using immutable Maps (yet), and would otherwise mutate referenced objects */
        .merge(node)
        .value(),
    )
    .thru(mapNodes)
    .value();

const useNodeMap = <Data>(partialUpdates = true) => {
  const [nodes, setNodeMapState] = useState<NodeMap<Data>>(new Map());

  const update = (next: NodeMap<Data>) => {
    const draft = partialUpdates
      ? mergeNodes(nodes, next)
      : next; /* draft does not merge correctly at the moment. it works for determining changes, but does not represent the next state correctly and is therefore not used when setting the next state. */
    const hasChanges = _([...draft.entries()]).some(
      ([key, node]) => !_.isEqual(nodes.get(key), node),
    );

    if (hasChanges) {
      setNodeMapState((prev) => new Map([...prev, ...next]));
    }
  };

  const reset = () => {
    setNodeMapState(new Map());
  };

  return { nodes, update, reset };
};

export default useNodeMap;
