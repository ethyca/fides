import { Button, Icons } from "fidesui";

import styles from "./NodeActions.module.scss";

interface NodeActionsProps {
  onAddNode?: () => void;
}

const NodeActions = ({ onAddNode }: NodeActionsProps) => (
  <div className={styles.actions}>
    <Button
      type="primary"
      size="small"
      icon={<Icons.Add size={16} />}
      onClick={onAddNode}
      aria-label="Add node"
      data-testid="add-node-btn"
      className={styles.addButton}
    />
  </div>
);

export default NodeActions;
