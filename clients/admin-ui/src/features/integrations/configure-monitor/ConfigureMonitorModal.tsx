import { UseDisclosureReturn } from "fidesui";

import FidesSpinner from "~/features/common/FidesSpinner";
import AddModal from "~/features/configure-consent/AddModal";
import ConfigureMonitorDatabasesForm from "~/features/integrations/configure-monitor/ConfigureMonitorDatabasesForm";
import ConfigureMonitorForm from "~/features/integrations/configure-monitor/ConfigureMonitorForm";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  MonitorConfig,
} from "~/types/api";

const ConfigureMonitorModal = ({
  isOpen,
  onClose,
  formStep,
  onAdvance,
  monitor,
  isEditing,
  integration,
  integrationOption,
}: Pick<UseDisclosureReturn, "isOpen" | "onClose"> & {
  formStep: number;
  monitor?: MonitorConfig;
  isEditing?: boolean;
  onAdvance: (m: MonitorConfig) => void;
  integration: ConnectionConfigurationResponse;
  integrationOption: ConnectionSystemTypeMap;
}) => (
  <AddModal
    title={
      monitor?.name
        ? `Configure ${monitor.name}`
        : "Configure discovery monitor"
    }
    isOpen={isOpen}
    onClose={onClose}
  >
    {formStep === 0 && (
      <ConfigureMonitorForm
        monitor={monitor}
        onClose={onClose}
        onAdvance={onAdvance}
        integrationOption={integrationOption}
      />
    )}
    {formStep === 1 &&
      (monitor ? (
        <ConfigureMonitorDatabasesForm
          monitor={monitor}
          isEditing={isEditing}
          onClose={onClose}
          integrationKey={integration.key}
        />
      ) : (
        <FidesSpinner />
      ))}
  </AddModal>
);

export default ConfigureMonitorModal;
