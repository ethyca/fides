import { FormikProvider, useFormik } from "formik";

import ConfirmCloseModal from "~/features/common/modals/ConfirmCloseModal";
import SSOProviderForm, {
  defaultInitialValues,
  getSSOProviderFormValidationSchema,
  useSSOProviderSubmit,
} from "~/features/openid-authentication/SSOProviderForm";

const AddSSOProviderModal = ({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) => {
  const { handleSubmit } = useSSOProviderSubmit({ onClose });

  const formik = useFormik({
    initialValues: defaultInitialValues,
    onSubmit: handleSubmit,
    validationSchema: getSSOProviderFormValidationSchema(false),
  });

  return (
    <FormikProvider value={formik}>
      <ConfirmCloseModal
        open={isOpen}
        onClose={onClose}
        getIsDirty={() => formik.dirty}
        centered
        destroyOnClose
        title="Add SSO Provider"
        footer={null}
      >
        <SSOProviderForm onClose={onClose} />
      </ConfirmCloseModal>
    </FormikProvider>
  );
};

export default AddSSOProviderModal;
