import { Modal } from "fidesui";

import OAuthClientForm from "./OAuthClientForm";

interface CreateOAuthClientModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated?: (clientId: string, secret: string) => void;
}

const CreateOAuthClientModal = ({
  isOpen,
  onClose,
  onCreated,
}: CreateOAuthClientModalProps) => (
  <Modal
    open={isOpen}
    onCancel={onClose}
    title="Create API client"
    centered
    footer={null}
    width={720}
    data-testid="create-oauth-client-modal"
  >
    <OAuthClientForm onClose={onClose} onCreated={onCreated} />
  </Modal>
);

export default CreateOAuthClientModal;
