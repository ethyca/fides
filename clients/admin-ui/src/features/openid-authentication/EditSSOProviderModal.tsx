import AddModal from "~/features/configure-consent/AddModal";
import { OpenIDProviderForm } from "~/features/openid-authentication/OpenIDProviderForm";
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
      <OpenIDProviderForm openIDProvider={openIDProvider} onClose={onClose} />
    </AddModal>
  );


export default EditSSOProviderModal;
