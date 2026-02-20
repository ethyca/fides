import {
  Button,
  ChakraUseDisclosureReturn as UseDisclosureReturn,
} from "fidesui";
import { useMemo, useState } from "react";

import FormModal from "~/features/common/modals/FormModal";
import ConfigureIntegrationForm from "~/features/integrations/add-integration/ConfigureIntegrationForm";
import { useGetSystemLinksQuery } from "~/features/integrations/system-links.slice";
import { SaasConnectionTypes } from "~/features/integrations/types/SaasConnectionTypes";
import useIntegrationOption from "~/features/integrations/useIntegrationOption";
import { ConnectionConfigurationResponse } from "~/types/api";

const ConfigureIntegrationModal = ({
  isOpen,
  onClose,
  connection,
  description,
}: Pick<UseDisclosureReturn, "isOpen" | "onClose"> & {
  connection: ConnectionConfigurationResponse;
  description: React.ReactNode;
}) => {
  const [formState, setFormState] = useState<{
    dirty: boolean;
    isValid: boolean;
    submitForm: () => void;
    loading: boolean;
  } | null>(null);

  const connectionOption = useIntegrationOption(
    connection.connection_type,
    connection?.saas_config?.type as SaasConnectionTypes,
  );

  // Fetch currently linked systems for editing
  const { data: systemLinksData } = useGetSystemLinksQuery(connection.key, {
    skip: !connection.key,
  });

  // Get the currently linked system (prefer monitoring link type, fallback to first link)
  const initialSystemFidesKey = useMemo(() => {
    if (!systemLinksData || systemLinksData.length === 0) {
      return undefined;
    }
    const monitoringLink = systemLinksData.find(
      (link) => link.link_type === "monitoring",
    );
    return (
      monitoringLink?.system_fides_key || systemLinksData[0]?.system_fides_key
    );
  }, [systemLinksData]);

  const handleSave = () => {
    if (formState && formState.submitForm) {
      formState.submitForm();
    }
  };

  const modalFooter = (
    <div className="flex w-full justify-between">
      <Button onClick={onClose} data-testid="cancel-btn">
        Cancel
      </Button>
      <Button
        type="primary"
        onClick={handleSave}
        disabled={!formState || !formState.isValid || !formState.dirty}
        loading={formState?.loading}
        data-testid="save-btn"
      >
        Save
      </Button>
    </div>
  );

  return (
    <FormModal
      title={`Manage ${connection?.name} integration`}
      isOpen={isOpen}
      onClose={onClose}
      footer={modalFooter}
    >
      <ConfigureIntegrationForm
        connection={connection}
        connectionOption={connectionOption!}
        onClose={onClose}
        description={description}
        onFormStateChange={setFormState}
        initialSystemFidesKey={initialSystemFidesKey}
      />
    </FormModal>
  );
};

export default ConfigureIntegrationModal;
