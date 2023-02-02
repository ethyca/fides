import { Button, Divider, Heading, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useState } from "react";

import { CustomSelect, CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import {
  useCreateStorageMutation,
  useCreateStorageSecretsMutation,
  useGetStorageDetailsQuery,
} from "~/features/privacy-requests/privacy-requests.slice";

interface StorageDetails {
  type: string;
  details: {
    auth_method: string;
    bucket: string;
  };
  format: string;
}
interface SecretsStorageData {
  aws_access_key_id: string;
  aws_secret_access_key: string;
}

const S3StorageConfiguration = () => {
  const [authMethod, setAuthMethod] = useState("");
  const { data: storageDetails } = useGetStorageDetailsQuery("s3");
  const [saveStorageDetails] = useCreateStorageMutation();
  const [setStorageSecrets] = useCreateStorageSecretsMutation();
  const { errorAlert, successAlert } = useAlert();

  const initialValues = {
    type: "s3",
    details: {
      auth_method: storageDetails.auth_method ?? "",
      bucket: storageDetails.bucket ?? "",
    },
    format: storageDetails.format ?? "",
  };

  const initialSecretValues = {
    aws_access_key_id: "",
    aws_secret_access_key: "",
  };

  const handleSubmitStorageConfiguration = async (
    newValues: StorageDetails
  ) => {
    const payload = await saveStorageDetails({
      type: "s3",
      details: {
        auth_method: newValues.details.auth_method,
        bucket: newValues.details.bucket,
      },
      format: newValues.format,
    });

    if ("error" in payload) {
      errorAlert(
        getErrorMessage(payload.error),
        `Updating S3 storage details has failed due to the following:`
      );
    } else {
      setAuthMethod(newValues.details.auth_method);
      successAlert(`S3 storage credentials successfully updated.`);
    }
  };

  const handleSubmitStorageSecrets = async (newValues: SecretsStorageData) => {
    const payload = await setStorageSecrets({
      aws_access_key_id: newValues.aws_access_key_id,
      aws_secret_access_key: newValues.aws_secret_access_key,
    });
    if ("error" in payload) {
      errorAlert(
        getErrorMessage(payload.error),
        `Updating S3 storage secrets has failed due to the following:`
      );
    } else {
      successAlert(`S3 storage secrets successfully updated.`);
    }
  };

  return (
    <>
      <Heading fontSize="md" fontWeight="semibold" mt={10}>
        S3 storage configuration
      </Heading>
      <Stack>
        <Formik
          initialValues={initialValues}
          onSubmit={handleSubmitStorageConfiguration}
        >
          {({ isSubmitting, resetForm }) => (
            <Form>
              <Stack mt={5} spacing={5}>
                <CustomSelect
                  name="format"
                  label="Format"
                  options={[
                    { label: "json", value: "json" },
                    { label: "csv", value: "csv" },
                  ]}
                />
                <CustomSelect
                  name="auth_method"
                  label="Auth method"
                  options={[
                    { label: "secret_keys", value: "secret_keys" },
                    { label: "automatic", value: "automatic" },
                  ]}
                />
                <CustomTextInput
                  name="bucket"
                  label="Bucket"
                  placeholder="Optional"
                />
              </Stack>

              <Button
                onClick={() => resetForm()}
                mt={5}
                mr={2}
                size="sm"
                variant="outline"
              >
                Cancel
              </Button>
              <Button
                mt={5}
                disabled={isSubmitting}
                type="submit"
                colorScheme="primary"
                size="sm"
                data-testid="save-btn"
              >
                Save
              </Button>
            </Form>
          )}
        </Formik>
      </Stack>
      {authMethod === "secret_keys" ? (
        <>
          <Divider mt={5} />
          <Heading fontSize="md" fontWeight="semibold" mt={5}>
            Storage destination
          </Heading>
          Use the key returned in the last step to provide and authenticate your
          storage destination’s secrets:
          <Stack>
            <Formik
              initialValues={initialSecretValues}
              onSubmit={handleSubmitStorageSecrets}
            >
              {({ isSubmitting, resetForm }) => (
                <Form>
                  <Stack mt={5} spacing={5}>
                    <CustomTextInput
                      name="aws_access_key_ID"
                      label="AWS access key ID"
                    />

                    <CustomTextInput
                      name="aws_secret_access_key"
                      label="AWS secret access key"
                    />
                  </Stack>
                  <Button
                    onClick={() => resetForm()}
                    mt={5}
                    mr={2}
                    size="sm"
                    variant="outline"
                  >
                    Cancel
                  </Button>
                  <Button
                    mt={5}
                    disabled={isSubmitting}
                    type="submit"
                    colorScheme="primary"
                    size="sm"
                    data-testid="save-btn"
                  >
                    Save
                  </Button>
                </Form>
              )}
            </Formik>
          </Stack>
        </>
      ) : null}
    </>
  );
};

export default S3StorageConfiguration;
