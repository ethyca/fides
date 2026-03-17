import {
  Button,
  useChakraToast as useToast,
} from "fidesui";
import { Form, Formik } from "formik";
import * as Yup from "yup";

import { CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { ClientResponse } from "~/types/api";

import {
  useCreateOAuthClientMutation,
  useUpdateOAuthClientMutation,
} from "./oauth-clients.slice";
import ScopePicker from "./ScopePicker";

export interface OAuthClientFormValues {
  name: string;
  description: string;
  scopes: string[];
}

const validationSchema = Yup.object().shape({
  name: Yup.string().required().label("Name"),
  description: Yup.string().label("Description"),
  scopes: Yup.array().of(Yup.string()).label("Scopes"),
});

interface OAuthClientFormProps {
  /** When provided, the form is in edit mode for this client. */
  client?: ClientResponse;
  onClose: () => void;
  /** Called with the new client_id + plaintext secret after successful creation. */
  onCreated?: (clientId: string, secret: string) => void;
}

const OAuthClientForm = ({
  client,
  onClose,
  onCreated,
}: OAuthClientFormProps) => {
  const toast = useToast();
  const [createClient] = useCreateOAuthClientMutation();
  const [updateClient] = useUpdateOAuthClientMutation();

  const isEditing = !!client;

  const initialValues: OAuthClientFormValues = {
    name: client?.name ?? "",
    description: client?.description ?? "",
    scopes: client?.scopes ?? [],
  };

  const handleSubmit = async (values: OAuthClientFormValues) => {
    if (isEditing) {
      const result = await updateClient({
        client_id: client.client_id,
        name: values.name,
        description: values.description || undefined,
        scopes: values.scopes,
      });
      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
      } else {
        toast(successToastParams("API client updated."));
        // Stay on the page — no navigation after save
      }
    } else {
      const result = await createClient({
        name: values.name,
        description: values.description || undefined,
        scopes: values.scopes,
      });
      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
      } else {
        toast(
          successToastParams(
            "API client created. Copy the secret — it won't be shown again.",
          ),
        );
        onClose();
        if (onCreated && result.data) {
          onCreated(result.data.client_id, result.data.client_secret);
        }
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
            <div>
              <p className="text-sm font-medium mb-2">Scopes</p>
              <hr className="mb-3" />
              <ScopePicker name="scopes" />
            </div>
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
                {isEditing ? "Save changes" : "Create client"}
              </Button>
            </div>
          </div>
        </Form>
      )}
    </Formik>
  );
};

export default OAuthClientForm;
