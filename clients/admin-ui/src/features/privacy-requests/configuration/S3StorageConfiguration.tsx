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
import { S3SecretsDetails } from "~/features/privacy-requests/types";

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

const S3StorageConfiguration = ({ storageDetails }: SavedStorageDetails) => {
  const [authMethod, setAuthMethod] = useState("");
  const [saveStorageDetails] = useCreateStorageMutation();
  const [setStorageSecrets] = useCreateStorageSecretsMutation();

  const { handleError } = useAPIHelper();
  const message = useMessage();

  const [configForm] = Form.useForm();
  const [secretsForm] = Form.useForm();

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
      message.success(`S3 storage credentials successfully updated.`);
    }
  };

  const handleSubmitStorageSecrets = async (newValues: S3SecretsDetails) => {
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
      message.success(`S3 storage secrets successfully updated.`);
    }
  };

  return (
    <>
      <Typography.Title level={5} className="mt-10">
        S3 storage configuration
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
                { label: "secret_keys", value: "secret_keys" },
                { label: "automatic", value: "automatic" },
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
      {authMethod === "secret_keys" ? (
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
              <Form.Item name="aws_access_key_id" label="AWS access key ID">
                <Input />
              </Form.Item>
              <Form.Item
                name="aws_secret_access_key"
                label="AWS secret access key"
              >
                <Input.Password />
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
      ) : null}
    </>
  );
};

export default S3StorageConfiguration;
