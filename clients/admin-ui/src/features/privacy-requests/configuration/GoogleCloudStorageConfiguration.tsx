import {
  Button,
  Divider,
  Flex,
  Form,
  Input,
  Select,
  Typography,
  useMessage,
} from "fidesui";
import { useState } from "react";

import { isErrorResult } from "~/features/common/helpers";
import { useAPIHelper } from "~/features/common/hooks";
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
  const message = useMessage();

  const [configForm] = Form.useForm();
  const [secretsForm] = Form.useForm();

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
      message.success(`Google Cloud Storage credentials successfully updated.`);
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
      message.success(`Google Cloud Storage secrets successfully updated.`);
    }
  };

  return (
    <>
      <Typography.Title level={5} className="mt-10">
        Google Cloud Storage configuration
      </Typography.Title>
      <Form
        form={configForm}
        initialValues={initialValues}
        onFinish={handleSubmitStorageConfiguration}
        key={JSON.stringify(initialValues)}
        layout="vertical"
      >
        <Flex vertical className="mt-5">
          <Form.Item
            name="format"
            label="Format"
            rules={[{ required: true, message: "Format is required" }]}
          >
            <Select
              aria-label="Format"
              options={[
                { label: "json", value: "json" },
                { label: "csv", value: "csv" },
              ]}
              data-testid="format"
            />
          </Form.Item>
          <Form.Item
            name="auth_method"
            label="Auth method"
            rules={[{ required: true, message: "Auth method is required" }]}
          >
            <Select
              aria-label="Auth method"
              options={[
                {
                  label: "Service Account Keys",
                  value: "service_account_keys",
                },
                { label: "Application Default Credentials", value: "adc" },
              ]}
              data-testid="auth_method"
            />
          </Form.Item>
          <Form.Item
            name="bucket"
            label="Bucket"
            rules={[{ required: true, message: "Bucket is required" }]}
          >
            <Input data-testid="bucket" />
          </Form.Item>
        </Flex>

        <Button onClick={() => configForm.resetFields()} className="mr-2 mt-5">
          Cancel
        </Button>
        <Button
          htmlType="submit"
          className="mt-5"
          type="primary"
          data-testid="save-btn"
        >
          Save
        </Button>
      </Form>
      {authMethod === "service_account_keys" && (
        <>
          <Divider className="mt-5" />
          <Typography.Title level={5} className="mt-5">
            Storage destination
          </Typography.Title>
          <Form
            form={secretsForm}
            initialValues={initialSecretValues}
            onFinish={handleSubmitStorageSecrets}
            layout="vertical"
          >
            <Flex vertical className="mt-5">
              <Form.Item name="type" label="Type">
                <Input />
              </Form.Item>
              <Form.Item name="project_id" label="Project ID">
                <Input />
              </Form.Item>
              <Form.Item name="private_key_id" label="Private key ID">
                <Input.Password />
              </Form.Item>
              <Form.Item name="private_key" label="Private key">
                <Input.Password />
              </Form.Item>
              <Form.Item name="client_email" label="Client email">
                <Input />
              </Form.Item>
              <Form.Item name="client_id" label="Client ID">
                <Input />
              </Form.Item>
              <Form.Item name="auth_uri" label="Auth URI">
                <Input />
              </Form.Item>
              <Form.Item name="token_uri" label="Token URI">
                <Input />
              </Form.Item>
              <Form.Item
                name="auth_provider_x509_cert_url"
                label="Auth provider x509 cert URL"
              >
                <Input />
              </Form.Item>
              <Form.Item
                name="client_x509_cert_url"
                label="Client x509 cert URL"
              >
                <Input />
              </Form.Item>
              <Form.Item name="universe_domain" label="Universe domain">
                <Input />
              </Form.Item>
            </Flex>
            <div className="mt-10">
              <Button
                onClick={() => secretsForm.resetFields()}
                className="mr-2 mt-5"
              >
                Cancel
              </Button>
              <Button
                htmlType="submit"
                type="primary"
                className="mt-5"
                data-testid="save-btn"
              >
                Save
              </Button>
            </div>
          </Form>
        </>
      )}
    </>
  );
};

export default GoogleCloudStorageConfiguration;
