import { Heading, Stack, Button, Divider } from "@fidesui/react";
import { Formik, Form } from "formik";
import { useState } from "react";
import { CustomSelect, CustomTextInput } from "~/features/common/form/inputs";

const S3StorageConfiguration = () => {
  const [authMethod, setAuthMethod] = useState("");
  const initialValues = {
    format: "",
  };

  const handleSubmitStorageConfiguration = (newValues) => {
    console.log("newVals", newValues);
    setAuthMethod(newValues.auth_method);
  };

  const handleSubmitStorageSecrets = (newValues) => {
    console.log("newvals2", newValues);
  };

  const handleCancel = () => {
    console.log("cancel");
  };

  const CONFIG_FORM_ID = "s3-privacy-requests-storage-configuration-config";
  const KEYS_FORM_ID = "s3-privacy-requests-storage-configuration-keys";

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
          {({ isSubmitting }) => (
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

              <Button onClick={handleCancel} mr={2} size="sm" variant="outline">
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
              initialValues={initialValues}
              onSubmit={handleSubmitStorageSecrets}
            >
              {({ isSubmitting }) => (
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
                    onClick={handleCancel}
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
