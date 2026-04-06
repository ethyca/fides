import { FormikProvider, useFormik } from "formik";

import ConfirmCloseModal from "~/features/common/modals/ConfirmCloseModal";
import { OpenIDProvider } from "~/types/api/models/OpenIDProvider";

import SSOProviderForm, {
  getSSOProviderFormValidationSchema,
  transformOrganizationToFormValues,
  useSSOProviderSubmit,
} from "~/features/openid-authentication/SSOProviderForm";

const EditSSOProviderModal = ({
  isOpen,
  onClose,
  openIDProvider,
}: {
  isOpen: boolean;
  onClose: () => void;
  openIDProvider: OpenIDProvider;
}) => {
  const { handleSubmit } = useSSOProviderSubmit({ openIDProvider, onClose });

  const formik = useFormik({
    initialValues: transformOrganizationToFormValues(openIDProvider),
    onSubmit: handleSubmit,
    validationSchema: getSSOProviderFormValidationSchema(true),
    enableReinitialize: true,
  });

  return (
    <FormikProvider value={formik}>
      <ConfirmCloseModal
        open={isOpen}
        onClose={onClose}
        getIsDirty={() => formik.dirty}
        centered
        destroyOnClose
        title="Edit SSO Provider"
        footer={null}
      >
        <SSOProviderForm onClose={onClose} isEditMode />
      </ConfirmCloseModal>
    </FormikProvider>
  );
};

export default EditSSOProviderModal;
