import { Button, Flex, Radio, Switch, Text } from "fidesui";

import { ActionType, Reachability, TraversalPreviewResponse } from "../types";
import styles from "./CanvasHeader.module.scss";
import { PropertyPicker } from "./PropertyPicker";

interface Props {
  propertyKey: string | null;
  actionType: ActionType;
  showNotTouched: boolean;
  payload: TraversalPreviewResponse | undefined;
  onPropertyChange: (key: string) => void;
  onActionChange: (action: ActionType) => void;
  onShowNotTouchedChange: (show: boolean) => void;
  onRegenerate: () => void;
}

const summarize = (payload: TraversalPreviewResponse | undefined) => {
  if (!payload) {
    return "";
  }
  const reach = payload.integrations.filter(
    (i) => i.reachability !== Reachability.UNREACHABLE,
  ).length;
  const skipped = payload.integrations.length - reach;
  const manual = payload.manual_tasks.length;
  return `${reach} system${reach === 1 ? "" : "s"} will be queried, ${manual} manual review${manual === 1 ? "" : "s"}, ${skipped} not touched`;
};

export const CanvasHeader = ({
  propertyKey,
  actionType,
  showNotTouched,
  payload,
  onPropertyChange,
  onActionChange,
  onShowNotTouchedChange,
  onRegenerate,
}: Props) => (
  <Flex
    align="center"
    gap="middle"
    justify="space-between"
    className={styles.root}
    data-testid="canvas-header"
  >
    <Flex align="center" gap="middle">
      <PropertyPicker value={propertyKey} onChange={onPropertyChange} />
      <Radio.Group
        value={actionType}
        onChange={(e) => onActionChange(e.target.value)}
        data-testid="action-type-toggle"
        className={styles.actionToggle}
      >
        <Radio.Button value={ActionType.ACCESS}>Access</Radio.Button>
        <Radio.Button value={ActionType.ERASURE}>Erasure</Radio.Button>
      </Radio.Group>
      <Switch
        checked={showNotTouched}
        onChange={onShowNotTouchedChange}
        data-testid="show-not-touched"
      />
      <Text type="secondary" className="text-xs">
        Show not touched
      </Text>
    </Flex>
    <Flex align="center" gap="middle">
      {payload && (
        <Text type="secondary" className="text-xs">
          {summarize(payload)}
        </Text>
      )}
      <Button
        onClick={onRegenerate}
        data-testid="regenerate"
        disabled={!propertyKey}
      >
        Regenerate
      </Button>
    </Flex>
  </Flex>
);
