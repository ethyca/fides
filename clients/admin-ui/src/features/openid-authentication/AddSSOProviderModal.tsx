import { UseDisclosureReturn } from "fidesui";

import FormModal from "~/features/common/modals/FormModal";
import SSOProviderForm from "~/features/openid-authentication/SSOProviderForm";

const AddSSOProviderModal = ({
  isOpen,
  onClose,
}: Pick<UseDisclosureReturn, "isOpen" | "onClose">) => (
  <FormModal isOpen={isOpen} onClose={onClose} title="Add SSO Provider">
    <SSOProviderForm onClose={onClose} />
  </FormModal>
);

export default AddSSOProviderModal;
