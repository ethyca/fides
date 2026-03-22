import { Handle, Node, NodeProps, Position } from "@xyflow/react";

import styles from "./JunctionNode.module.scss";

// eslint-disable-next-line @typescript-eslint/no-empty-interface
export interface JunctionNodeData extends Record<string, unknown> {}

export type JunctionNodeType = Node<JunctionNodeData, "junctionNode">;

/**
 * A minimal passthrough node that visually bridges condition and constraint
 * columns so that dagre places them in separate ranks.
 */
const JunctionNode = (_props: NodeProps<JunctionNodeType>) => (
  <div className={styles.junction} data-testid="junction-node">
    <Handle type="target" position={Position.Left} className={styles.handle} />
    <Handle type="source" position={Position.Right} className={styles.handle} />
  </div>
);

export default JunctionNode;
