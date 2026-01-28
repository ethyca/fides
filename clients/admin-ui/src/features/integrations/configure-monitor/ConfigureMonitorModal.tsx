import {
  ChakraUseDisclosureReturn as UseDisclosureReturn,
  useChakraToast as useToast,
} from "fidesui";

import FidesSpinner from "~/features/common/FidesSpinner";
import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import FormModal from "~/features/common/modals/FormModal";
import { DEFAULT_TOAST_PARAMS } from "~/features/common/toast";
import {
  useCreateIdentityProviderMonitorMutation,
  useGetAvailableDatabasesByConnectionQuery,
  usePutDiscoveryMonitorMutation,
  usePutIdentityProviderMonitorMutation,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";
import ConfigureMonitorDatabasesForm from "~/features/integrations/configure-monitor/ConfigureMonitorDatabasesForm";
import ConfigureMonitorForm from "~/features/integrations/configure-monitor/ConfigureMonitorForm";
import ConfigureWebsiteMonitorForm from "~/features/integrations/configure-monitor/ConfigureWebsiteMonitorForm";
import {
  ConnectionConfigurationResponseWithSystemKey,
  ConnectionSystemTypeMap,
  ConnectionType,
  EditableMonitorConfig,
  MonitorFrequency,
} from "~/types/api";
import { isErrorResult, RTKResult } from "~/types/errors";

const TIMEOUT_DELAY = 5000;
const TIMEOUT_COPY =
  "Saving this monitor is taking longer than expected. Fides will continue processing it in the background, and you can check back later to view the updates.";

const WEBSITE_MONITOR_NOW_SCANNING_MESSAGE =
  "Your monitor has been created and is now scanning your website. Once the monitor is finished scanning, results can be found in the action center.";

const WEBSITE_MONITOR_NOT_SCHEDULED_MESSAGE = `Your monitor has been created with no schedule.  Select "Scan" in the table below to begin scanning your website.`;

const ConfigureMonitorModal = ({
  isOpen,
  onClose,
  formStep,
  onAdvance,
  monitor,
  isEditing,
  integration,
  integrationOption,
  isWebsiteMonitor,
}: Pick<UseDisclosureReturn, "isOpen" | "onClose"> & {
  formStep: number;
  monitor?: EditableMonitorConfig;
  isEditing?: boolean;
  onAdvance: (m: EditableMonitorConfig) => void;
  integration: ConnectionConfigurationResponseWithSystemKey;
  integrationOption: ConnectionSystemTypeMap;
  isWebsiteMonitor?: boolean;
}) => {
  const isOktaIntegration = integration.connection_type === ConnectionType.OKTA;

  const [putMonitorMutationTrigger, { isLoading: isSubmittingRegular }] =
    usePutDiscoveryMonitorMutation();

  const [
    createIdentityProviderMonitorTrigger,
    { isLoading: isSubmittingOktaCreate },
  ] = useCreateIdentityProviderMonitorMutation();

  const [
    putIdentityProviderMonitorTrigger,
    { isLoading: isSubmittingOktaUpdate },
  ] = usePutIdentityProviderMonitorMutation();

  let isSubmitting: boolean;
  if (isOktaIntegration) {
    isSubmitting = isEditing ? isSubmittingOktaUpdate : isSubmittingOktaCreate;
  } else {
    isSubmitting = isSubmittingRegular;
  }

  const { data: databases } = useGetAvailableDatabasesByConnectionQuery({
    page: 1,
    size: 25,
    connection_config_key: integration.key,
  });

  const databasesAvailable = !!databases && !!databases.total;

  const toast = useToast();

  const { successAlert, errorAlert } = useAlert();

  const handleSubmit = async (values: EditableMonitorConfig) => {
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

    // Use Identity Provider Monitor endpoint for Okta, otherwise use regular endpoint
    if (isOktaIntegration) {
      // Transform MonitorConfig to IdentityProviderMonitorConfig format
      const oktaPayload = {
        name: values.name,
        key: values.key ?? undefined,
        provider: "okta" as const,
        connection_config_key: integration.key,
        enabled: values.enabled ?? true,
        execution_start_date: values.execution_start_date ?? undefined,
        execution_frequency: values.execution_frequency ?? undefined,
        classify_params: values.classify_params ?? {},
      };
      // Use PUT for editing, POST for creating
      if (isEditing) {
        result = await putIdentityProviderMonitorTrigger(oktaPayload);
      } else {
        result = await createIdentityProviderMonitorTrigger(oktaPayload);
      }
    } else {
      result = await putMonitorMutationTrigger(values);
    }

    if (result) {
      clearTimeout(timeout);
      if (isErrorResult(result)) {
        errorAlert(getErrorMessage(result.error), "Error creating monitor");
        return;
      }
      if (isEditing) {
        successAlert("Monitor updated successfully");
        onClose();
        return;
      }
      if (isWebsiteMonitor) {
        successAlert(
          values.execution_frequency === MonitorFrequency.NOT_SCHEDULED
            ? WEBSITE_MONITOR_NOT_SCHEDULED_MESSAGE
            : WEBSITE_MONITOR_NOW_SCANNING_MESSAGE,
        );
        onClose();
        return;
      }
      successAlert("Monitor created successfully");
      onClose();
    }
  };

  if (isWebsiteMonitor) {
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
          url={(integration.secrets as unknown as { url: string })?.url ?? ""}
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
          integrationSystem={integration?.system_key}
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
