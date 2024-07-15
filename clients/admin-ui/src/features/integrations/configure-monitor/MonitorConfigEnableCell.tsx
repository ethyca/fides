import { CellContext } from "@tanstack/react-table";

import { EnableCell } from "~/features/common/table/v2/cells";
import { usePutDiscoveryMonitorMutation } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { MonitorConfig } from "~/types/api";

const MODAL_TITLE = "Disabling monitor";
const MODAL_TEXT =
  "You are about to disable this monitor. If you continue, it will no longer scan automatically.";

export const MonitorConfigEnableCell = ({
  row,
  getValue,
}: CellContext<MonitorConfig, boolean | undefined>) => {
  const [putMonitor] = usePutDiscoveryMonitorMutation();

  const onToggle = async (toggleValue: boolean) =>
    putMonitor({
      ...row.original,
      enabled: toggleValue,
    });

  const enabled = getValue()!;

  return (
    <EnableCell
      enabled={enabled}
      onToggle={onToggle}
      title={MODAL_TITLE}
      message={MODAL_TEXT}
    />
  );
};
