import { AntButton as Button, Box, Divider, Heading, Stack } from "fidesui";
import { Form, Formik } from "formik";
import { useState } from "react";

import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import { CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import { storageTypes } from "~/features/privacy-requests/constants";
import {
  useCreateStorageMutation,
  useCreateStorageSecretsMutation,
} from "~/features/privacy-requests/privacy-requests.slice";
import { GCSSecretsDetails } from "~/features/privacy-requests/types";

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

const GoogleCloudStorageConfiguration = ({
  storageDetails,
}: SavedStorageDetails) => {
  const [authMethod, setAuthMethod] = useState("");
  const [saveStorageDetails] = useCreateStorageMutation();
  const [setStorageSecrets] = useCreateStorageSecretsMutation();

  const { handleError } = useAPIHelper();
  const { successAlert } = useAlert();

  const initialValues = {
    type: storageTypes.gcs,
    auth_method: storageDetails?.details?.auth_method ?? "",
    bucket: storageDetails?.details?.bucket ?? "",
    format: storageDetails?.format ?? "",
  };

  const initialSecretValues = {
    type: "",
    project_id: "",
    private_key_id: "",
    private_key: "",
    client_email: "",
    client_id: "",
    auth_uri: "",
    token_uri: "",
    auth_provider_x509_cert_url: "",
    client_x509_cert_url: "",
    universe_domain: "",
  };

  const handleSubmitStorageConfiguration = async (
    newValues: StorageDetails["storageDetails"],
  ) => {
    const result = await saveStorageDetails({
      type: storageTypes.gcs,
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
      successAlert(`Google Cloud Storage credentials successfully updated.`);
    }
  };

  const handleSubmitStorageSecrets = async (newValues: GCSSecretsDetails) => {
    let cleanedKey = newValues.private_key.trim();
    // Replace escaped newlines with actual newlines
    if (cleanedKey.includes("\\n")) {
      cleanedKey = cleanedKey.replace(/\\n/g, "\n");
    }

    const result = await setStorageSecrets({
      details: {
        type: newValues.type,
        project_id: newValues.project_id,
        private_key_id: newValues.private_key_id,
        private_key: cleanedKey,
        client_email: newValues.client_email,
        client_id: newValues.client_id,
        auth_uri: newValues.auth_uri,
        token_uri: newValues.token_uri,
        auth_provider_x509_cert_url: newValues.auth_provider_x509_cert_url,
        client_x509_cert_url: newValues.client_x509_cert_url,
        universe_domain: newValues.universe_domain,
      },
      type: storageTypes.gcs,
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      successAlert(`Google Cloud Storage secrets successfully updated.`);
    }
  };

  return (
    <>
      <Heading fontSize="md" fontWeight="semibold" mt={10}>
        Google Cloud Storage configuration
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
                <ControlledSelect
                  name="format"
                  label="Format"
                  options={[
                    { label: "json", value: "json" },
                    { label: "csv", value: "csv" },
                  ]}
                  data-testid="format"
                  isRequired
                />
                <ControlledSelect
                  name="auth_method"
                  label="Auth method"
                  options={[
                    {
                      label: "Service Account Keys",
                      value: "service_account_keys",
                    },
                    { label: "Application Default Credentials", value: "adc" },
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
      {authMethod === "service_account_keys" && (
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
                    <CustomTextInput name="type" label="Type" />
                    <CustomTextInput name="project_id" label="Project ID" />
                    <CustomTextInput
                      name="private_key_id"
                      label="Private key ID"
                      type="password"
                    />
                    <CustomTextInput
                      name="private_key"
                      label="Private key"
                      type="password"
                    />
                    <CustomTextInput name="client_email" label="Client email" />
                    <CustomTextInput name="client_id" label="Client ID" />
                    <CustomTextInput name="auth_uri" label="Auth URI" />
                    <CustomTextInput name="token_uri" label="Token URI" />
                    <CustomTextInput
                      name="auth_provider_x509_cert_url"
                      label="Auth provider x509 cert URL"
                    />
                    <CustomTextInput
                      name="client_x509_cert_url"
                      label="Client x509 cert URL"
                    />
                    <CustomTextInput
                      name="universe_domain"
                      label="Universe domain"
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
      )}
    </>
  );
};

export default GoogleCloudStorageConfiguration;
