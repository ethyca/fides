import AddModal from "~/features/configure-consent/AddModal";
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
  <AddModal isOpen={isOpen} onClose={onClose} title="Edit SSO Provider">
    <SSOProviderForm openIDProvider={openIDProvider} onClose={onClose} />
  </AddModal>
);


export default EditSSOProviderModal;
