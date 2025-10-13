import { EnableCell } from "~/features/common/table/cells/EnableCell";
import { usePutDiscoveryMonitorMutation } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { MonitorConfig } from "~/types/api";

const MODAL_TITLE = "Disabling monitor";
const MODAL_TEXT =
  "You are about to disable this monitor. If you continue, it will no longer scan automatically.";

export const MonitorConfigEnableCell = ({
  record,
}: {
  record: MonitorConfig;
}) => {
  const [putMonitor] = usePutDiscoveryMonitorMutation();
  const handleToggle = async (toggleValue: boolean) =>
    putMonitor({
      ...record,
      enabled: toggleValue,
    });
  const { enabled } = record;

  return (
    <EnableCell
      enabled={!!enabled}
      onToggle={handleToggle}
      title={MODAL_TITLE}
      message={MODAL_TEXT}
    />
  );
};
