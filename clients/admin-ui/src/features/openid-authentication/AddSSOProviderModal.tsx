import { UseDisclosureReturn } from "fidesui";

import AddModal from "~/features/configure-consent/AddModal";
import { OpenIDProviderForm } from "~/features/openid-authentication/OpenIDProviderForm";

const AddSSOProviderModal = ({
    isOpen,
    onClose,
  }: Pick<UseDisclosureReturn, "isOpen" | "onClose">) => (
    <AddModal isOpen={isOpen} onClose={onClose} title="Add SSO Provider">
      <OpenIDProviderForm onClose={onClose} />
    </AddModal>
  );


export default AddSSOProviderModal;
