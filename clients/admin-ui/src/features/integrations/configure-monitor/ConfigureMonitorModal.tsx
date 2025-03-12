import { UseDisclosureReturn, useToast } from "fidesui";

import FidesSpinner from "~/features/common/FidesSpinner";
import useQueryResultToast from "~/features/common/form/useQueryResultToast";
import FormModal from "~/features/common/modals/FormModal";
import { DEFAULT_TOAST_PARAMS } from "~/features/common/toast";
import {
  useGetAvailableDatabasesByConnectionQuery,
  usePutDiscoveryMonitorMutation,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";
import ConfigureMonitorDatabasesForm from "~/features/integrations/configure-monitor/ConfigureMonitorDatabasesForm";
import ConfigureMonitorForm from "~/features/integrations/configure-monitor/ConfigureMonitorForm";
import ConfigureWebsiteMonitorForm from "~/features/integrations/configure-monitor/ConfigureWebsiteMonitorForm";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  ConnectionType,
  MonitorConfig,
} from "~/types/api";
import { isErrorResult, RTKResult } from "~/types/errors";

const TIMEOUT_DELAY = 5000;
const TIMEOUT_COPY =
  "Saving this monitor is taking longer than expected. Fides will continue processing it in the background, and you can check back later to view the updates.";

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

  const { data: databases } = useGetAvailableDatabasesByConnectionQuery({
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
          description: TIMEOUT_COPY,
        });
        onClose();
      }
    }, TIMEOUT_DELAY);
    result = await putMonitorMutationTrigger(values);
    if (result) {
      clearTimeout(timeout);
      toastResult(result);
      if (!isErrorResult(result)) {
        onClose();
      }
    }
  };

  if (integrationOption.identifier === ConnectionType.WEBSITE) {
    return (
      <FormModal
        title={
          monitor?.name
            ? `Configure ${monitor.name}`
            : "Configure website monitor"
        }
        isOpen={isOpen}
        onClose={onClose}
      >
        <ConfigureWebsiteMonitorForm
          monitor={monitor}
          // @ts-ignore - "secrets" is typed as "null"
          url={integration.secrets!.url as string}
          onClose={onClose}
          onSubmit={handleSubmit}
        />
      </FormModal>
    );
  }

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
