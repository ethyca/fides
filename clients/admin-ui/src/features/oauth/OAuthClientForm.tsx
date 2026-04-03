import { Button, useMessage } from "fidesui";
import { Form, Formik } from "formik";
import * as Yup from "yup";

import { CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";

import { useCreateOAuthClientMutation } from "./oauth-clients.slice";

export interface OAuthClientFormValues {
  name: string;
  description: string;
  scopes: string[];
}

const validationSchema = Yup.object().shape({
  name: Yup.string().required().label("Name"),
  description: Yup.string().label("Description"),
});

interface OAuthClientFormProps {
  onClose: () => void;
  /** Called with the new client_id + plaintext secret after successful creation. */
  onCreated?: (clientId: string, secret: string) => void;
}

const OAuthClientForm = ({ onClose, onCreated }: OAuthClientFormProps) => {
  const message = useMessage();
  const [createClient] = useCreateOAuthClientMutation();

  const initialValues: OAuthClientFormValues = {
    name: "",
    description: "",
    scopes: [],
  };

  const handleSubmit = async (values: OAuthClientFormValues) => {
    const result = await createClient({
      name: values.name,
      description: values.description || undefined,
      scopes: values.scopes,
    });
    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
    } else {
      message.success("API client created.");
      onClose();
      if (onCreated && result.data) {
        onCreated(result.data.client_id, result.data.client_secret);
      }
    }
  };

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      validationSchema={validationSchema}
      onSubmit={handleSubmit}
    >
      {({ dirty, isValid, isSubmitting }) => (
        <Form data-testid="oauth-client-form">
          <div className="flex flex-col gap-4">
            <CustomTextInput
              name="name"
              label="Name"
              variant="stacked"
              isRequired
              data-testid="client-name-input"
            />
            <CustomTextInput
              name="description"
              label="Description"
              variant="stacked"
              data-testid="client-description-input"
            />
            <div className="flex justify-end gap-3">
              <Button
                htmlType="button"
                onClick={onClose}
                data-testid="cancel-btn"
              >
                Cancel
              </Button>
              <Button
                htmlType="submit"
                type="primary"
                disabled={!dirty || !isValid}
                loading={isSubmitting}
                data-testid="save-btn"
              >
                Create client
              </Button>
            </div>
          </div>
        </Form>
      )}
    </Formik>
  );
};

export default OAuthClientForm;
