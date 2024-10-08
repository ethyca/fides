import { AntButton as Button, Box, Divider, Heading, Stack } from "fidesui";
import { Form, Formik } from "formik";
import { useState } from "react";

import { CustomSelect, CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import { storageTypes } from "~/features/privacy-requests/constants";
import {
  useCreateStorageMutation,
  useCreateStorageSecretsMutation,
} from "~/features/privacy-requests/privacy-requests.slice";

interface SavedStorageDetails {
  storageDetails: {
    details: {
      auth_method: string;
      bucket: string;
    };
    format: string;
  };
}
interface StorageDetails {
  storageDetails: {
    auth_method: string;
    bucket: string;
    format: string;
  };
}
interface SecretsStorageData {
  aws_access_key_id: string;
  aws_secret_access_key: string;
}

const S3StorageConfiguration = ({ storageDetails }: SavedStorageDetails) => {
  const [authMethod, setAuthMethod] = useState("");
  const [saveStorageDetails] = useCreateStorageMutation();
  const [setStorageSecrets] = useCreateStorageSecretsMutation();

  const { handleError } = useAPIHelper();
  const { successAlert } = useAlert();

  const initialValues = {
    type: storageTypes.s3,
    auth_method: storageDetails?.details?.auth_method ?? "",
    bucket: storageDetails?.details?.bucket ?? "",
    format: storageDetails?.format ?? "",
  };

  const initialSecretValues = {
    aws_access_key_id: "",
    aws_secret_access_key: "",
  };

  const handleSubmitStorageConfiguration = async (
    newValues: StorageDetails["storageDetails"],
  ) => {
    const result = await saveStorageDetails({
      type: storageTypes.s3,
      details: {
        auth_method: newValues.auth_method,
        bucket: newValues.bucket,
      },
      format: newValues.format,
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      setAuthMethod(newValues.auth_method);
      successAlert(`S3 storage credentials successfully updated.`);
    }
  };

  const handleSubmitStorageSecrets = async (newValues: SecretsStorageData) => {
    const result = await setStorageSecrets({
      details: {
        aws_access_key_id: newValues.aws_access_key_id,
        aws_secret_access_key: newValues.aws_secret_access_key,
      },
      type: storageTypes.s3,
    });

    if (isErrorResult(result)) {
      handleError(result.error);
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
          enableReinitialize
        >
          {({ isSubmitting, handleReset }) => (
            <Form>
              <Stack mt={5} spacing={5}>
                <CustomSelect
                  name="format"
                  label="Format"
                  options={[
                    { label: "json", value: "json" },
                    { label: "csv", value: "csv" },
                  ]}
                  data-testid="format"
                  isRequired
                />
                <CustomSelect
                  name="auth_method"
                  label="Auth method"
                  options={[
                    { label: "secret_keys", value: "secret_keys" },
                    { label: "automatic", value: "automatic" },
                  ]}
                  data-testid="auth_method"
                  isRequired
                />
                <CustomTextInput
                  data-testid="bucket"
                  name="bucket"
                  label="Bucket"
                  isRequired
                />
              </Stack>

              <Button onClick={() => handleReset()} className="mr-2 mt-5">
                Cancel
              </Button>
              <Button
                htmlType="submit"
                className="mt-5"
                disabled={isSubmitting}
                type="primary"
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
          <Stack>
            <Formik
              initialValues={initialSecretValues}
              onSubmit={handleSubmitStorageSecrets}
            >
              {({ isSubmitting, handleReset }) => (
                <Form>
                  <Stack mt={5} spacing={5}>
                    <CustomTextInput
                      name="aws_access_key_id"
                      label="AWS access key ID"
                    />

                    <CustomTextInput
                      name="aws_secret_access_key"
                      label="AWS secret access key"
                      type="password"
                    />
                  </Stack>
                  <Box mt={10}>
                    <Button onClick={() => handleReset()} className="mr-2 mt-5">
                      Cancel
                    </Button>
                    <Button
                      disabled={isSubmitting}
                      htmlType="submit"
                      type="primary"
                      className="mt-5"
                      data-testid="save-btn"
                    >
                      Save
                    </Button>
                  </Box>
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
