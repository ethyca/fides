import { Modal } from "fidesui";

import SSOProviderForm from "~/features/openid-authentication/SSOProviderForm";
import { OpenIDProvider } from "~/types/api/models/OpenIDProvider";

const EditSSOProviderModal = ({
  isOpen,
  onClose,
  openIDProvider,
}: {
  isOpen: boolean;
  onClose: () => void;
  openIDProvider: OpenIDProvider;
}) => (
  <Modal
    open={isOpen}
    onCancel={onClose}
    centered
    destroyOnClose
    title="Edit SSO Provider"
    footer={null}
  >
    <SSOProviderForm openIDProvider={openIDProvider} onClose={onClose} />
  </Modal>
);

export default EditSSOProviderModal;
