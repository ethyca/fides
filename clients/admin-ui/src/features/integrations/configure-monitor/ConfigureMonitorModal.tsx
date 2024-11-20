import { UseDisclosureReturn, useToast } from "fidesui";

import FidesSpinner from "~/features/common/FidesSpinner";
import useQueryResultToast from "~/features/common/form/useQueryResultToast";
import FormModal from "~/features/common/modals/FormModal";
import { DEFAULT_TOAST_PARAMS } from "~/features/common/toast";
import {
  useGetDatabasesByConnectionQuery,
  usePutDiscoveryMonitorMutation,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";
import ConfigureMonitorDatabasesForm from "~/features/integrations/configure-monitor/ConfigureMonitorDatabasesForm";
import ConfigureMonitorForm from "~/features/integrations/configure-monitor/ConfigureMonitorForm";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  MonitorConfig,
} from "~/types/api";
import { isErrorResult, RTKResult } from "~/types/errors";

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
}) => {
  const [putMonitorMutationTrigger, { isLoading: isSubmitting }] =
    usePutDiscoveryMonitorMutation();

  const { data: databases } = useGetDatabasesByConnectionQuery({
    page: 1,
    size: 25,
    connection_config_key: integration.key,
  });

  const databasesAvailable = !!databases && !!databases.total;

  const toast = useToast();

  const { toastResult } = useQueryResultToast({
    defaultSuccessMsg: `Monitor ${
      isEditing ? "updated" : "created"
    } successfully`,
    defaultErrorMsg: `A problem occurred while ${
      isEditing ? "updating" : "creating"
    } this monitor`,
  });

  const handleSubmit = async (values: MonitorConfig) => {
    let result: RTKResult | undefined;
    const timeout = setTimeout(() => {
      if (!result) {
        toast({
          ...DEFAULT_TOAST_PARAMS,
          status: "info",
          description:
            "This monitor is taking an unusually long time to save.  Fides will continue to process it in the background, and you can return to view it later.",
        });
        onClose();
      }
    }, 5000);
    result = await putMonitorMutationTrigger(values);
    if (result) {
      clearTimeout(timeout);
      toastResult(result);
      if (!isErrorResult(result)) {
        onClose();
      }
    }
  };

  return (
    <FormModal
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
          onSubmit={handleSubmit}
          isSubmitting={isSubmitting}
          databasesAvailable={databasesAvailable}
          integrationOption={integrationOption}
        />
      )}
      {formStep === 1 &&
        (monitor ? (
          <ConfigureMonitorDatabasesForm
            monitor={monitor}
            isEditing={isEditing}
            isSubmitting={isSubmitting}
            onSubmit={handleSubmit}
            onClose={onClose}
            integrationKey={integration.key}
          />
        ) : (
          <FidesSpinner />
        ))}
    </FormModal>
  );
};

export default ConfigureMonitorModal;
