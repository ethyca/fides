import { Button, ButtonGroup, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { lazy } from "yup";

import {
  CustomCheckbox,
  CustomSelect,
  CustomTextInput,
} from "~/features/common/form/inputs";
import {
  findActionFromPolicyKey,
  generateValidationSchemaFromAction,
} from "~/features/privacy-requests/form/helpers";
import { useGetPrivacyCenterConfigQuery } from "~/features/privacy-requests/privacy-requests.slice";
import {
  fides__api__schemas__privacy_center_config__CustomPrivacyRequestField,
  IdentityInputs,
  PrivacyRequestCreate,
  PrivacyRequestOption,
} from "~/types/api";

export type PrivacyRequestSubmitFormValues = PrivacyRequestCreate & {
  is_verified: boolean;
};

const defaultInitialValues: PrivacyRequestSubmitFormValues = {
  is_verified: false,
  policy_key: "",
  identity: {},
};

const IdentityFields = ({
  identityInputs,
}: {
  identityInputs?: IdentityInputs;
}) => {
  if (!identityInputs) {
    return null;
  }
  return (
    <>
      {identityInputs.email ? (
        <CustomTextInput
          name="identity.email"
          label="User email address"
          isRequired={identityInputs.email === IdentityInputs.email.REQUIRED}
          variant="stacked"
        />
      ) : null}
      {identityInputs.phone ? (
        <CustomTextInput
          name="identity.phone_number"
          label="User phone number"
          isRequired={identityInputs.phone === IdentityInputs.phone.REQUIRED}
          variant="stacked"
        />
      ) : null}
    </>
  );
};

const CustomFields = ({
  customFieldInputs,
}: {
  customFieldInputs?: Record<
    string,
    fides__api__schemas__privacy_center_config__CustomPrivacyRequestField
  >;
}) => {
  if (!customFieldInputs) {
    return null;
  }
  const allInputs = Object.entries(customFieldInputs);
  return (
    <>
      {allInputs.map(([fieldName, fieldInfo]) =>
        !fieldInfo.hidden ? (
          <CustomTextInput
            name={`custom_privacy_request_fields.${fieldName}.value`}
            key={fieldName}
            label={fieldInfo.label}
            isRequired={fieldInfo.required}
            variant="stacked"
          />
        ) : null
      )}
    </>
  );
};

const SubmitPrivacyRequestForm = ({
  onSubmit,
  onCancel,
}: {
  onSubmit: (values: PrivacyRequestSubmitFormValues) => void;
  onCancel: () => void;
}) => {
  const { data: config } = useGetPrivacyCenterConfigQuery();

  return (
    <Formik
      initialValues={defaultInitialValues}
      onSubmit={onSubmit}
      validationSchema={() =>
        lazy((values) =>
          generateValidationSchemaFromAction(
            findActionFromPolicyKey(values.policy_key, config?.actions)
          )
        )
      }
    >
      {({ values, dirty, isValid, isSubmitting, setFieldValue }) => {
        const currentAction = findActionFromPolicyKey(
          values.policy_key,
          config?.actions
        );

        const handleResetCustomFields = (e: any) => {
          // when selecting a new request type, populate the Formik state with
          // labels and default values for the corresponding custom fields
          const newAction = findActionFromPolicyKey(e.value, config?.actions);
          if (!newAction?.custom_privacy_request_fields) {
            setFieldValue(`custom_privacy_request_fields`, undefined);
            return;
          }
          const newCustomFields = Object.entries(
            newAction.custom_privacy_request_fields
          )
            .map(([fieldName, fieldInfo]) => ({
              [fieldName]: {
                label: fieldInfo.label,
                value: fieldInfo.default_value,
              },
            }))
            .reduce((acc, next) => ({ ...acc, ...next }), {});
          setFieldValue(`custom_privacy_request_fields`, newCustomFields);
        };

        return (
          <Form>
            <Stack spacing={6} mb={2}>
              <CustomSelect
                name="policy_key"
                label="Request type"
                options={
                  config?.actions.map((action: PrivacyRequestOption) => ({
                    label: action.title,
                    value: action.policy_key,
                  })) ?? []
                }
                onChange={(e: any) => handleResetCustomFields(e)}
                variant="stacked"
                isRequired
              />
              <IdentityFields identityInputs={currentAction?.identity_inputs} />
              <CustomFields
                customFieldInputs={currentAction?.custom_privacy_request_fields}
              />
              <CustomCheckbox
                name="is_verified"
                label="I confirm that I have verified this user information"
              />
              <ButtonGroup alignSelf="end" spacing={0}>
                <Button variant="outline" size="sm" onClick={onCancel} mr={4}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  colorScheme="primary"
                  size="sm"
                  isDisabled={!values.is_verified || !dirty || !isValid}
                  isLoading={isSubmitting}
                  data-testid="submit-btn"
                >
                  Submit
                </Button>
              </ButtonGroup>
            </Stack>
          </Form>
        );
      }}
    </Formik>
  );
};

export default SubmitPrivacyRequestForm;
