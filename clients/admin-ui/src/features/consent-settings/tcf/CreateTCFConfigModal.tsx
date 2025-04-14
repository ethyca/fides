import {
  AntButton as Button,
  AntSpace as Space,
  Text,
  useToast,
} from "fidesui";
import { Form, Formik } from "formik";
import * as Yup from "yup";

import { CustomTextInput } from "~/features/common/form/inputs";
import FormModal from "~/features/common/modals/FormModal";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useCreateTCFConfigurationMutation } from "~/features/consent-settings/tcf/tcf-config.slice";
import { isErrorResult } from "~/types/errors";

import { getErrorMessage } from "../../common/helpers";

interface CreateTCFConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (configId: string) => void;
}

const ValidationSchema = Yup.object().shape({
  name: Yup.string().required().label("Name"),
});

export const CreateTCFConfigModal = ({
  isOpen,
  onClose,
  onSuccess,
}: CreateTCFConfigModalProps) => {
  const toast = useToast();
  const [createTCFConfiguration] = useCreateTCFConfigurationMutation();

  const handleSubmit = async (values: { name: string }) => {
    const result = await createTCFConfiguration({ name: values.name });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(successToastParams("Successfully created TCF configuration"));
      onSuccess?.(result.data.id);
      onClose();
    }
  };

  return (
    <FormModal
      title="Create a new TCF configuration"
      isOpen={isOpen}
      onClose={onClose}
    >
      <Formik
        initialValues={{ name: "" }}
        onSubmit={handleSubmit}
        validationSchema={ValidationSchema}
      >
        {({ isValid, dirty }) => (
          <Form>
            <Space direction="vertical" size="small" className="w-full">
              <Text>
                TCF configurations allow you to define unique sets of publisher
                restrictions. These configurations can be added to privacy
                experiences.
              </Text>
              <CustomTextInput
                id="name"
                name="name"
                label="Name"
                isRequired
                variant="stacked"
              />
              <Space className="w-full justify-end pt-6">
                <Button onClick={onClose}>Cancel</Button>
                <Button
                  type="primary"
                  htmlType="submit"
                  disabled={!isValid || !dirty}
                >
                  Save
                </Button>
              </Space>
            </Space>
          </Form>
        )}
      </Formik>
    </FormModal>
  );
};
