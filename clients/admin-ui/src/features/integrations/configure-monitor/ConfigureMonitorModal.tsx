import { Spinner, UseDisclosureReturn } from "fidesui";
import { useMemo } from "react";

import AddModal from "~/features/configure-consent/AddModal";
import { useFetchDatabasesByConnectionMutation } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import ConfigureMonitorDatabasesForm from "~/features/integrations/configure-monitor/ConfigureMonitorDatabasesForm";
import ConfigureMonitorForm from "~/features/integrations/configure-monitor/ConfigureMonitorForm";
import DatabaseSelectionV2 from "~/features/integrations/configure-monitor/DatabaseSelectionV2";
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
  integration,
  integrationOption,
}: Pick<UseDisclosureReturn, "isOpen" | "onClose"> & {
  formStep: number;
  monitor?: MonitorConfig;
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
    <DatabaseSelectionV2 integrationKey={integration.key} />
    {/* {formStep === 0 && (
        <ConfigureMonitorForm
          monitor={monitor}
          onClose={onClose}
          onAdvance={onAdvance}
          integrationOption={integrationOption}
        />
      )}
      {formStep === 1 &&
        (monitor ? (
          <ConfigureMonitorDatabasesForm monitor={monitor} onClose={onClose} />
        ) : (
          <Spinner />
        ))} */}
  </AddModal>
);

export default ConfigureMonitorModal;
