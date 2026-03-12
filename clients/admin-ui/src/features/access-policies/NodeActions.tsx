import classNames from "classnames";
import { Button, Flex, Icons, Typography } from "fidesui";

import styles from "./NodeActions.module.scss";

interface NodeActionsProps {
  onAddNode?: () => void;
  onAddCondition?: () => void;
  onAddAction?: () => void;
  showAddAction?: boolean;
}

const NodeActions = ({
  onAddNode,
  onAddCondition,
  onAddAction,
  showAddAction = true,
}: NodeActionsProps) => (
  <div className={styles.actions}>
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
          Condition
        </Typography.Text>
      </Flex>
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
            Action
          </Typography.Text>
        </Flex>
      )}
    </div>
  </div>
);

export default NodeActions;
