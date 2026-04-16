import { Button, Flex, useMessage } from "fidesui";
import { Form, Formik } from "formik";
import * as Yup from "yup";

import { CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { useHasPermission } from "~/features/common/Restrict";
import { ClientResponse, ScopeRegistryEnum } from "~/types/api";

import {
  useCreateOAuthClientMutation,
  useUpdateOAuthClientMutation,
} from "./oauth-clients.slice";

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
  const message = useMessage();
  const [createClient] = useCreateOAuthClientMutation();
  const [updateClient] = useUpdateOAuthClientMutation();
  const canUpdate = useHasPermission([ScopeRegistryEnum.CLIENT_UPDATE]);

  const initialValues: OAuthClientFormValues = {
    name: client?.name ?? "",
    description: client?.description ?? "",
    scopes: client?.scopes ?? [],
  };

  const handleSubmit = async (values: OAuthClientFormValues) => {
    if (client) {
      const result = await updateClient({
        path: { client_id: client.client_id },
        body: {
          name: values.name,
          description: values.description || undefined,
          scopes: values.scopes,
        },
      });
      if (isErrorResult(result)) {
        message.error(getErrorMessage(result.error));
      } else {
        message.success("API client updated.");
        onClose();
      }
      return;
    }

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
          <Flex gap="middle" vertical>
            <CustomTextInput
              name="name"
              label="Name"
              variant="stacked"
              isRequired
              data-testid="client-name-input"
              disabled={!canUpdate}
            />
            <CustomTextInput
              name="description"
              label="Description"
              variant="stacked"
              data-testid="client-description-input"
              disabled={!canUpdate}
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
                disabled={!dirty || !isValid || !canUpdate}
                loading={isSubmitting}
                data-testid="save-btn"
              >
                {client ? "Save changes" : "Create client"}
              </Button>
            </div>
          </Flex>
        </Form>
      )}
    </Formik>
  );
};

export default OAuthClientForm;
