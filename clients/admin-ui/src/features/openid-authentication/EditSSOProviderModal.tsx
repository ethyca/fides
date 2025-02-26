import FormModal from "~/features/common/modals/FormModal";
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
  <FormModal isOpen={isOpen} onClose={onClose} title="Edit SSO Provider">
    <SSOProviderForm openIDProvider={openIDProvider} onClose={onClose} />
  </FormModal>
);

export default EditSSOProviderModal;
