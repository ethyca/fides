import { Button, Radio, Switch } from "fidesui";

import { TraversalPreviewResponse } from "../types";
import PropertyPicker from "./PropertyPicker";

interface Props {
  propertyKey: string | null;
  actionType: "access" | "erasure";
  showNotTouched: boolean;
  payload: TraversalPreviewResponse | undefined;
  onPropertyChange: (key: string) => void;
  onActionChange: (action: "access" | "erasure") => void;
  onShowNotTouchedChange: (show: boolean) => void;
  onRegenerate: () => void;
}

const summarize = (payload: TraversalPreviewResponse | undefined) => {
  if (!payload) {
    return "";
  }
  const reach = payload.integrations.filter(
    (i) => i.reachability !== "unreachable",
  ).length;
  const skipped = payload.integrations.length - reach;
  const manual = payload.manual_tasks.length;
  return `${reach} system${reach === 1 ? "" : "s"} will be queried, ${manual} manual review${manual === 1 ? "" : "s"}, ${skipped} not touched`;
};

const CanvasHeader = ({
  propertyKey,
  actionType,
  showNotTouched,
  payload,
  onPropertyChange,
  onActionChange,
  onShowNotTouchedChange,
  onRegenerate,
}: Props) => (
  <div
    data-testid="canvas-header"
    style={{
      display: "flex",
      alignItems: "center",
      gap: 16,
      padding: "12px 16px",
      borderBottom: "1px solid var(--fidesui-color-border)",
      background: "var(--fidesui-color-bg-container)",
      position: "sticky",
      top: 0,
      zIndex: 10,
    }}
  >
    <PropertyPicker value={propertyKey} onChange={onPropertyChange} />
    <Radio.Group
      value={actionType}
      onChange={(e) => onActionChange(e.target.value)}
      data-testid="action-type-toggle"
    >
      <Radio.Button value="access">Access</Radio.Button>
      <Radio.Button value="erasure">Erasure</Radio.Button>
    </Radio.Group>
    <Switch
      checked={showNotTouched}
      onChange={onShowNotTouchedChange}
      data-testid="show-not-touched"
    />
    <span style={{ fontSize: 12, color: "var(--fidesui-color-text-tertiary)" }}>
      Show not touched
    </span>
    <span style={{ flex: 1 }} />
    {payload ? (
      <span
        style={{ fontSize: 12, color: "var(--fidesui-color-text-secondary)" }}
      >
        {summarize(payload)}
      </span>
    ) : null}
    <Button
      onClick={onRegenerate}
      data-testid="regenerate"
      disabled={!propertyKey}
    >
      Regenerate
    </Button>
  </div>
);

export default CanvasHeader;
