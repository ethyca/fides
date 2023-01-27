import { Button, Divider, Heading, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useState } from "react";

import { CustomSelect, CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import {
  useSetStorageDetailsMutation,
  useSetStorageSecretsMutation,
} from "~/features/privacy-requests/privacy-requests.slice";

interface StorageData {
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

const S3StorageConfiguration = ({
  details: { auth_method, bucket },
  format,
}: StorageData) => {
  const [authMethod, setAuthMethod] = useState("");
  const [setStorageDetails] = useSetStorageDetailsMutation();
  const [setStorageSecrets] = useSetStorageSecretsMutation();
  const { errorAlert, successAlert } = useAlert();
  const CONFIG_FORM_ID = "s3-privacy-requests-storage-configuration-config";
  const KEYS_FORM_ID = "s3-privacy-requests-storage-configuration-keys";

  const initialValues = {
    type: "s3",
    details: {
      auth_method: auth_method ?? "",
      bucket: bucket ?? "",
    },
    format: format ?? "",
  };

  const initialSecretValues = {
    aws_access_key_id: "",
    aws_secret_access_key: "",
  };

  const handleSubmitStorageConfiguration = async (newValues: StorageData) => {
    const payload = await setStorageDetails({
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
        `Configuring storage details has failed to save due to the following:`
      );
    } else {
      setAuthMethod(newValues.details.auth_method);
      successAlert(`Storage details saved successfully.`);
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
        `Configuring storage secrets has failed to save due to the following:`
      );
    } else {
      successAlert(`Storage secrets saved successfully.`);
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
            <Form id={CONFIG_FORM_ID}>
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

              <Button
                onClick={() => resetForm()}
                mr={2}
                size="sm"
                variant="outline"
              >
                Cancel
              </Button>
              <Button
                disabled={isSubmitting}
                type="submit"
                colorScheme="primary"
                size="sm"
                data-testid="save-btn"
                form={CONFIG_FORM_ID}
                isLoading={false}
              >
                Save
              </Button>
            </Form>
          )}
        </Formik>
      </Stack>
      {authMethod === "secret_keys" ? (
        <>
          <Divider />
          <Heading fontSize="md" fontWeight="semibold" mt={10}>
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
                <Form id={KEYS_FORM_ID}>
                  <CustomTextInput
                    name="aws_access_key_ID"
                    label="AWS access key ID"
                  />

                  <CustomTextInput
                    name="aws_secret_access_key"
                    label="AWS secret access key"
                  />

                  <Button
                    onClick={() => resetForm()}
                    mr={2}
                    size="sm"
                    variant="outline"
                  >
                    Cancel
                  </Button>
                  <Button
                    disabled={isSubmitting}
                    type="submit"
                    colorScheme="primary"
                    size="sm"
                    data-testid="save-btn"
                    form={KEYS_FORM_ID}
                    isLoading={false}
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
