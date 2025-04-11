import { Box, UseDisclosureReturn } from "fidesui";

import FormModal from "~/features/common/modals/FormModal";
import ConfigureIntegrationForm from "~/features/integrations/add-integration/ConfigureIntegrationForm";
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
  const connectionOption = useIntegrationOption(connection.connection_type);

  return (
    <FormModal
      title={`Manage ${connection?.name} integration`}
      isOpen={isOpen}
      onClose={onClose}
    >
      {description && (
        <Box
          padding="20px 24px"
          backgroundColor="gray.50"
          borderRadius="md"
          border="1px solid"
          borderColor="gray.200"
          fontSize="sm"
          marginTop="16px"
        >
          {description}
        </Box>
      )}
      <ConfigureIntegrationForm
        connection={connection}
        connectionOption={connectionOption!}
        onCancel={onClose}
      />
    </FormModal>
  );
};

export default ConfigureIntegrationModal;
