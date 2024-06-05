import { Spinner, UseDisclosureReturn } from "fidesui";

import AddModal from "~/features/configure-consent/AddModal";
import ConfigureMonitorDatabasesForm from "~/features/integrations/configure-monitor/ConfigureMonitorDatabasesForm";
import ConfigureMonitorForm from "~/features/integrations/configure-monitor/ConfigureMonitorForm";
import { MonitorConfig } from "~/types/api";

const ConfigureMonitorModal = ({
  isOpen,
  onClose,
  formStep,
  onAdvance,
  monitor,
}: Pick<UseDisclosureReturn, "isOpen" | "onClose"> & {
  formStep: number;
  monitor?: MonitorConfig;
  onAdvance: (m: MonitorConfig) => void;
}) => (
  <AddModal
    title={
      monitor ? `Configure ${monitor.name}` : "Configure discovery monitor"
    }
    isOpen={isOpen}
    onClose={onClose}
  >
    {formStep === 0 && (
      <ConfigureMonitorForm
        monitor={monitor}
        onClose={onClose}
        onAdvance={onAdvance}
      />
    )}
    {formStep === 1 &&
      (monitor ? (
        <ConfigureMonitorDatabasesForm monitor={monitor} onClose={onClose} />
      ) : (
        <Spinner />
      ))}
  </AddModal>
);

export default ConfigureMonitorModal;
