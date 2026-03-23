import classNames from "classnames";
import { Button, Flex, Icons, Typography } from "fidesui";

import styles from "./NodeActions.module.scss";

interface NodeActionsProps {
  onAddNode?: () => void;
  onAddCondition?: () => void;
  onAddAction?: () => void;
  onAddConstraint?: () => void;
  showAddCondition?: boolean;
  showAddAction?: boolean;
  showAddConstraint?: boolean;
  /** Position relative to the node. Default: "right". */
  position?: "right" | "bottom";
}

const NodeActions = ({
  onAddNode,
  onAddCondition,
  onAddAction,
  onAddConstraint,
  showAddCondition = true,
  showAddAction = true,
  showAddConstraint = true,
  position = "right",
}: NodeActionsProps) => (
  <div className={classNames(styles.actions, styles[position])}>
    <Button
      type="primary"
      size="small"
      icon={<Icons.Add size={16} />}
      onClick={onAddNode}
      aria-label="Add node"
      data-testid="add-node-btn"
      className={classNames(styles.iconButton, styles.addButton)}
    />
    <div className={styles.actionMenu}>
      {showAddCondition && (
        <Flex align="center" gap="small" className={styles.actionItem}>
          <Button
            type="text"
            size="small"
            icon={<Icons.SettingsAdjust size={16} />}
            onClick={onAddCondition}
            aria-label="Add condition"
            data-testid="add-condition-btn"
            className={classNames(styles.iconButton, styles.conditionButton)}
          />
          <Typography.Text className={styles.actionLabel}>
            Match
          </Typography.Text>
        </Flex>
      )}
      {showAddConstraint && (
        <Flex align="center" gap="small" className={styles.actionItem}>
          <Button
            type="text"
            size="small"
            icon={<Icons.Locked size={16} />}
            onClick={onAddConstraint}
            aria-label="Add constraint"
            data-testid="add-constraint-btn"
            className={classNames(styles.iconButton, styles.constraintButton)}
          />
          <Typography.Text className={styles.actionLabel}>
            Constraint
          </Typography.Text>
        </Flex>
      )}
      {showAddAction && (
        <Flex align="center" gap="small" className={styles.actionItem}>
          <Button
            type="text"
            size="small"
            icon={<Icons.Fork size={16} />}
            onClick={onAddAction}
            aria-label="Add action"
            data-testid="add-action-btn"
            className={classNames(styles.iconButton, styles.actionButton)}
          />
          <Typography.Text className={styles.actionLabel}>
            Decision
          </Typography.Text>
        </Flex>
      )}
    </div>
  </div>
);

export default NodeActions;
