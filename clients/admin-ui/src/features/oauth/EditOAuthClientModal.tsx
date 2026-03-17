import { Modal } from "fidesui";

import { ClientResponse } from "~/types/api";

import OAuthClientForm from "./OAuthClientForm";

interface EditOAuthClientModalProps {
  isOpen: boolean;
  onClose: () => void;
  client: ClientResponse;
}

const EditOAuthClientModal = ({
  isOpen,
  onClose,
  client,
}: EditOAuthClientModalProps) => (
  <Modal
    open={isOpen}
    onCancel={onClose}
    title="Edit API client"
    centered
    width={672}
    footer={null}
    data-testid="edit-oauth-client-modal"
  >
    <OAuthClientForm client={client} onClose={onClose} />
  </Modal>
);

export default EditOAuthClientModal;
