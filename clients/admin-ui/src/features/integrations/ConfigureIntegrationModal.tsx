import { UseDisclosureReturn } from "fidesui";

import AddModal from "~/features/configure-consent/AddModal";
import ConfigureIntegrationForm from "~/features/integrations/ConfigureIntegrationForm";
import { ConnectionConfigurationResponse } from "~/types/api";

const ConfigureIntegrationModal = ({
  isOpen,
  onClose,
  connection,
}: Pick<UseDisclosureReturn, "isOpen" | "onClose"> & {
  connection: ConnectionConfigurationResponse;
}) => (
  <AddModal title="Manage integration secret" isOpen={isOpen} onClose={onClose}>
    <ConfigureIntegrationForm connection={connection} onCancel={onClose} />
  </AddModal>
);

export default ConfigureIntegrationModal;
