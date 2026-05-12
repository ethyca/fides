import {
  Button,
  Flex,
  Icons,
  Radio,
  Statistic,
  Switch,
  Text,
  Tooltip,
} from "fidesui";

import { ActionType, Reachability, TraversalPreviewResponse } from "../types";
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

export const CanvasHeader = ({
  propertyKey,
  actionType,
  showNotTouched,
  payload,
  onPropertyChange,
  onActionChange,
  onShowNotTouchedChange,
  onRegenerate,
}: Props) => {
  const reach =
    payload?.integrations.filter(
      (i) => i.reachability !== Reachability.UNREACHABLE,
    ).length ?? 0;
  const skipped = (payload?.integrations.length ?? 0) - reach;
  const manual = payload?.manual_tasks.length ?? 0;
  return (
    <Flex vertical gap="small" className="py-3" data-testid="canvas-header">
      <Flex align="center" gap="middle" justify="space-between">
        <Flex align="center" gap="middle">
          <PropertyPicker value={propertyKey} onChange={onPropertyChange} />
          <Radio.Group
            value={actionType}
            onChange={(e) => onActionChange(e.target.value)}
            data-testid="action-type-toggle"
            className="shrink-0 whitespace-nowrap"
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
        <Tooltip title="Regenerate">
          <Button
            icon={<Icons.Renew />}
            onClick={onRegenerate}
            data-testid="regenerate"
            disabled={!propertyKey}
            aria-label="Regenerate"
          />
        </Tooltip>
      </Flex>
      <Flex
        gap="large"
        wrap
        align="baseline"
        className={payload ? undefined : "invisible"}
        aria-hidden={!payload}
      >
        <Flex align="baseline" gap="small">
          <Statistic value={reach} />
          <Text type="secondary">
            {reach === 1 ? "system" : "systems"} will be queried
          </Text>
        </Flex>
        <Flex align="baseline" gap="small">
          <Statistic value={manual} />
          <Text type="secondary">manual review{manual === 1 ? "" : "s"}</Text>
        </Flex>
        <Flex align="baseline" gap="small">
          <Statistic value={skipped} />
          <Text type="secondary">not touched</Text>
        </Flex>
      </Flex>
    </Flex>
  );
};
