import { Button, ButtonGroup, useToast, VStack } from "fidesui";
import { Form, Formik } from "formik";
import * as Yup from "yup";

import { CustomSelect, CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage } from "~/features/common/helpers";
import {
  usePatchDatastoreConnectionMutation,
  useUpdateDatastoreConnectionSecretsMutation,
} from "~/features/datastore-connections";
import { formatKey } from "~/features/datastore-connections/add-connection/helpers";
import {
  useGetAllSystemsQuery,
  usePatchSystemConnectionConfigsMutation,
} from "~/features/system";
import {
  AccessLevel,
  ConnectionConfigurationResponse,
  ConnectionType,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

type FormValues = {
  name: string;
  keyfile_creds?: string;
  description: string;
  system_fides_key?: string;
};

const validationSchema = Yup.object().shape({
  name: Yup.string().required().label("Name"),
  keyfile_creds: Yup.string().nullable().label("Keyfile credentials"),
  description: Yup.string().nullable().label("Description"),
});

const ConfigureIntegrationForm = ({
  connection,
  onCancel,
}: {
  connection?: ConnectionConfigurationResponse;
  onCancel: () => void;
}) => {
  const [
    updateConnectionSecretsMutationTrigger,
    { isLoading: secretsIsLoading },
  ] = useUpdateDatastoreConnectionSecretsMutation();
  const [patchDatastoreConnectionsTrigger, { isLoading: patchIsLoading }] =
    usePatchDatastoreConnectionMutation();
  const [patchSystemConnectionsTrigger, { isLoading: systemPatchIsLoading }] =
    usePatchSystemConnectionConfigsMutation();

  const { data: allSystems } = useGetAllSystemsQuery();

  const systemOptions = allSystems?.map((s) => ({
    label: s.name ?? s.fides_key,
    value: s.fides_key,
  }));

  const isLoading = secretsIsLoading || patchIsLoading || systemPatchIsLoading;

  const initialValues: FormValues = {
    name: connection?.name ?? "",
    description: connection?.description ?? "",
  };

  const toast = useToast();

  const isEditing = !!connection;

  const handleSubmit = async (values: FormValues) => {
    const connectionPayload = isEditing
      ? {
          ...connection,
          disabled: connection.disabled ?? false,
          name: values.name,
          description: values.description,
        }
      : {
          name: values.name,
          key: formatKey(values.name),
          connection_type: ConnectionType.BIGQUERY,
          access: AccessLevel.READ,
          disabled: false,
          description: values.description,
        };
    // if system is attached, use patch request that attaches to system
    let patchResult;
    if (values.system_fides_key) {
      patchResult = await patchSystemConnectionsTrigger({
        systemFidesKey: values.system_fides_key,
        connectionConfigs: [connectionPayload],
      });
    } else {
      patchResult = await patchDatastoreConnectionsTrigger(connectionPayload);
    }
    if (isErrorResult(patchResult)) {
      const patchErrorMsg = getErrorMessage(
        patchResult.error,
        `A problem occurred while ${
          isEditing ? "updating" : "creating"
        } this integration. Please try again.`
      );
      toast({ status: "error", description: patchErrorMsg });
    } else {
      toast({
        status: "success",
        description: `Integration ${
          isEditing ? "updated" : "created"
        } successfully`,
      });
    }
    // if provided, update secrets with separate request
    if (values.keyfile_creds) {
      const secretsResult = await updateConnectionSecretsMutationTrigger({
        connection_key: connectionPayload.key,
        secrets: {
          keyfile_creds: values.keyfile_creds,
        },
      });
      if (isErrorResult(secretsResult)) {
        const secretsErrorMsg = getErrorMessage(
          secretsResult.error,
          `An error occurred while ${
            isEditing ? "updating" : "creating"
          } this integration secret.  Please try again.`
        );
        toast({ status: "error", description: secretsErrorMsg });
      } else {
        toast({
          status: "success",
          description: `Integration secret ${
            isEditing ? "updated" : "created"
          } successfully`,
        });
      }
    }
    onCancel();
  };
  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={validationSchema}
    >
      {({ dirty, isValid, resetForm }) => (
        <Form>
          <VStack alignItems="start" spacing={6} mt={4}>
            <CustomTextInput
              id="name"
              name="name"
              label="Name"
              variant="stacked"
              isRequired
            />
            <CustomTextInput
              type="password"
              id="keyfile_creds"
              name="keyfile_creds"
              label="Keyfile credentials (JSON)"
              variant="stacked"
            />
            <CustomTextInput
              id="description"
              name="description"
              label="Description"
              variant="stacked"
            />
            {!isEditing && (
              <CustomSelect
                id="system_fides_key"
                name="system_fides_key"
                options={systemOptions ?? []}
                label="System"
                tooltip="The system to associate with the integration"
                variant="stacked"
              />
            )}
            <ButtonGroup size="sm" width="100%" justifyContent="space-between">
              <Button
                variant="outline"
                onClick={() => {
                  onCancel();
                  resetForm();
                }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                isDisabled={!dirty || !isValid}
                isLoading={isLoading}
                data-testid="save-btn"
              >
                Update
              </Button>
            </ButtonGroup>
          </VStack>
        </Form>
      )}
    </Formik>
  );
};

export default ConfigureIntegrationForm;
