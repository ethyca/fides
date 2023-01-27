import { Button, Divider,Heading, Stack } from "@fidesui/react";
import { Form,Formik } from "formik";
import { useEffect, useState } from "react";

import { CustomSelect, CustomTextInput } from "~/features/common/form/inputs";
import {
  useGetStorageDetailsQuery,
  useSetStorageDetailsMutation,
  useSetStorageSecretsMutation,
} from "~/features/privacy-requests/privacy-requests.slice";

const S3StorageConfiguration = () => {
  const [authMethod, setAuthMethod] = useState("");
  const [setStorageDetails] = useSetStorageDetailsMutation();
  const [setStorageSecrets] = useSetStorageSecretsMutation();
  const initialValues = {
    format: "",
  };

  // on load, check to see if we already have this info saved
  useEffect(() => {
    const { data: existingData, isLoading: isLoadingStorageDetailsData } =
      useGetStorageDetailsQuery("s3");

    console.log("exist", existingData);
    console.log("isloading", isLoadingStorageDetailsData);
  }, []);

  const handleSubmitStorageConfiguration = async (newValues) => {
    console.log("newVals", newValues);
    setAuthMethod(newValues.auth_method);

    // helpers.setSubmitting(true);
    setSelected(value);

    const payload = await setStorageDetails({
      //   active_default_storage_type: value,
    });
    if ("error" in payload) {
      errorAlert(
        getErrorMessage(payload.error),
        `Configuring storage details has failed to save due to the following:`
      );
    } else {
      successAlert(`Storage details saved successfully.`);
    }
    // helpers.setSubmitting(false);

    //     PUT /storage/default/{storage_type}  body should look something like:
    //  {
    // 	"type": "s3",
    // 	"details": {
    //   		"auth_method": "secret_keys",
    //   		"bucket": "my_bucket",
    // 	},
    // 	"format": "json"
    //   }
  };

  const handleSubmitStorageSecrets = async (newValues) => {
    console.log("newvals2", newValues);

    // helpers.setSubmitting(true);

    const payload = await setStorageSecrets({
      //   active_default_storage_type: value,
    });
    if ("error" in payload) {
      errorAlert(
        getErrorMessage(payload.error),
        `Configuring storage secrets has failed to save due to the following:`
      );
    } else {
      successAlert(`Storage secrets saved successfully.`);
    }
    // helpers.setSubmitting(false);

    //     for config secrets:
    // PUT /storage/default/{storage_type}/secret body will look like:
    // { "aws_access_key_id" : "my_access_key_id",
    //    "aws_secret_access_key": "my_secret_access_key"
    // }
  };

  const handleCancel = () => {
    console.log("cancel");
    // Unclear in designs what cancel does?
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
