import { UseDisclosureReturn } from "fidesui";

import AddModal from "~/features/configure-consent/AddModal";
import ConfigureIntegrationForm from "~/features/integrations/add-integration/ConfigureIntegrationForm";
import useIntegrationOption from "~/features/integrations/useIntegrationOption";
import { ConnectionConfigurationResponse } from "~/types/api";

const ConfigureIntegrationModal = ({
  isOpen,
  onClose,
  connection,
}: Pick<UseDisclosureReturn, "isOpen" | "onClose"> & {
  connection: ConnectionConfigurationResponse;
}) => {
  const connectionOption = useIntegrationOption(connection.connection_type);

  return (
    <AddModal
      title="Manage integration secret"
      isOpen={isOpen}
      onClose={onClose}
    >
      <ConfigureIntegrationForm
        connection={connection}
        connectionOption={connectionOption!}
        onCancel={onClose}
      />
    </AddModal>
  );
};

export default ConfigureIntegrationModal;
