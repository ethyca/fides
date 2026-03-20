import {
  ChakraUseDisclosureReturn as UseDisclosureReturn,
  Modal,
} from "fidesui";

import SSOProviderForm from "~/features/openid-authentication/SSOProviderForm";

const AddSSOProviderModal = ({
  isOpen,
  onClose,
}: Pick<UseDisclosureReturn, "isOpen" | "onClose">) => (
  <Modal
    open={isOpen}
    onCancel={onClose}
    centered
    destroyOnClose
    title="Add SSO Provider"
    footer={null}
  >
    <SSOProviderForm onClose={onClose} />
  </Modal>
);

export default AddSSOProviderModal;
