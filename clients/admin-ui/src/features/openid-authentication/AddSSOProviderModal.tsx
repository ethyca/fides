import { UseDisclosureReturn } from "fidesui";

import AddModal from "~/features/configure-consent/AddModal";
import SSOProviderForm from "~/features/openid-authentication/SSOProviderForm";

const AddSSOProviderModal = ({
    isOpen,
    onClose,
  }: Pick<UseDisclosureReturn, "isOpen" | "onClose">) => (
    <AddModal isOpen={isOpen} onClose={onClose} title="Add SSO Provider">
      <SSOProviderForm onClose={onClose} />
    </AddModal>
  );


export default AddSSOProviderModal;
