import { UseDisclosureReturn } from "fidesui";

import FormModal from "~/features/common/modals/FormModal";
import ConfigureIntegrationForm from "~/features/integrations/add-integration/ConfigureIntegrationForm";
import { SaasConnectionTypes } from "~/features/integrations/types/SaasConnectionTypes";
import useIntegrationOption from "~/features/integrations/useIntegrationOption";
import { ConnectionConfigurationResponse, ConnectionType } from "~/types/api";

const ConfigureIntegrationModal = ({
  isOpen,
  onClose,
  connection,
  description,
}: Pick<UseDisclosureReturn, "isOpen" | "onClose"> & {
  connection: ConnectionConfigurationResponse;
  description: React.ReactNode;
}) => {
  const connectionOption = useIntegrationOption(
    connection.connection_type === ConnectionType.SAAS
      ? ConnectionType.SAAS
      : connection.connection_type,
    connection?.saas_config?.type as SaasConnectionTypes,
  );

  return (
    <FormModal
      title={`Manage ${connection?.name} integration`}
      isOpen={isOpen}
      onClose={onClose}
    >
      <ConfigureIntegrationForm
        connection={connection}
        connectionOption={connectionOption!}
        onCancel={onClose}
        description={description}
      />
    </FormModal>
  );
};

export default ConfigureIntegrationModal;
