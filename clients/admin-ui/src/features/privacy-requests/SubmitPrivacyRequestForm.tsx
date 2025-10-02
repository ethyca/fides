import {
  AntButton as Button,
  AntForm as Form,
  LinkIcon,
  LocationSelect,
  Stack,
  useClipboard,
  useToast,
} from "fidesui";
import { Form as FormikForm, Formik, useField } from "formik";
import { lazy } from "yup";
import * as Yup from "yup";

import { FormikTextInput } from "~/features/common/form/FormikTextInput";
import { CustomCheckbox, CustomTextInput } from "~/features/common/form/inputs";
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

import { ControlledSelect } from "../common/form/ControlledSelect";

/**
 * Mirror location type from backend
 */
export type LocationCustomPrivacyRequestField = {
  label: string;
  required?: boolean | null;
  default_value?: string | null;
  hidden?: boolean | null;
  query_param_key?: string | null;
  field_type: "location";
  ip_geolocation_hint?: boolean | null;
};

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
  identityInputs?: IdentityInputs | null;
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
          isRequired={identityInputs.email === "required"}
          variant="stacked"
        />
      ) : null}
      {identityInputs.phone ? (
        <CustomTextInput
          name="identity.phone_number"
          label="User phone number"
          isRequired={identityInputs.phone === "required"}
          variant="stacked"
        />
      ) : null}
    </>
  );
};

const LocationSelectInput = (props: {
  label: string;
  name: string;
  required: boolean;
}) => {
  const { label, required, name } = props;
  const [initialField, meta, helpers] = useField(props);
  const isInvalid = !!(meta.touched && meta.error);
  const { setValue } = helpers;
  const { value } = {
    ...initialField,
    value: initialField.value ?? "",
  };

  return (
    <Form.Item
      label={label}
      name={name}
      required={required ?? undefined}
      layout="vertical"
      validateStatus={isInvalid ? "error" : undefined}
    >
      <LocationSelect
        key={name}
        value={value}
        onChange={(newValue) => {
          if (newValue) {
            setValue(newValue);
          }
        }}
      />
    </Form.Item>
  );
};
const CustomFields = ({
  customFieldInputs,
}: {
  customFieldInputs?: Record<
    string,
    | fides__api__schemas__privacy_center_config__CustomPrivacyRequestField
    | LocationCustomPrivacyRequestField
  > | null;
}) => {
  if (!customFieldInputs) {
    return null;
  }
  const allInputs = Object.entries(customFieldInputs);
  return (
    <>
      {allInputs.map(([fieldName, fieldInfo]) => {
        /* checking for object key should not be necessarry when backend types are updated */
        return "field_type" in fieldInfo &&
          fieldInfo.field_type === "location" ? (
          <LocationSelectInput
            name={fieldName}
            key={fieldName}
            label={fieldInfo.label}
            required={Boolean(fieldInfo.required)}
          />
        ) : (
          <FormikTextInput
            name={`custom_privacy_request_fields.${fieldName}.value`}
            key={fieldName}
            label={fieldInfo.label}
            required={Boolean(fieldInfo.required)}
          />
        );
      })}
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
            findActionFromPolicyKey(values.policy_key, config?.actions),
          ),
        )
      }
    >
      {({ values, dirty, isValid, isSubmitting, setFieldValue }) => {
        const currentAction = findActionFromPolicyKey(
          values.policy_key,
          config?.actions,
        );

        const handleResetCustomFields = (value: string) => {
          // when selecting a new request type, populate the Formik state with
          // labels and default values for the corresponding custom fields
          const newAction = findActionFromPolicyKey(value, config?.actions);
          if (!newAction?.custom_privacy_request_fields) {
            setFieldValue(`custom_privacy_request_fields`, undefined);
            return;
          }
          const newCustomFields = Object.entries(
            newAction.custom_privacy_request_fields,
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
          <FormikForm>
            <Stack spacing={6} mb={2}>
              <ControlledSelect
                name="policy_key"
                label="Request type"
                options={
                  config?.actions.map((action: PrivacyRequestOption) => ({
                    label: action.title,
                    value: action.policy_key,
                  })) ?? []
                }
                onChange={handleResetCustomFields}
                layout="stacked"
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
              <div className="flex gap-4 self-end">
                <Button onClick={onCancel}>Cancel</Button>
                <Button
                  htmlType="submit"
                  type="primary"
                  disabled={!values.is_verified || !dirty || !isValid}
                  loading={isSubmitting}
                  data-testid="submit-btn"
                >
                  Create
                </Button>
              </div>
            </Stack>
          </FormikForm>
        );
      }}
    </Formik>
  );
};

export const CopyPrivacyRequestLinkForm = ({
  onSubmit,
  onCancel,
  privacyCenterUrl,
}: {
  onSubmit: (values: { identity: { email: string } }) => void;
  onCancel: () => void;
  privacyCenterUrl: string;
}) => {
  const { onCopy } = useClipboard("");
  const toast = useToast();
  return (
    <Formik
      initialValues={{ identity: { email: "" } }}
      onSubmit={(values) => {
        onCopy(
          `${privacyCenterUrl}?email=${encodeURIComponent(values.identity.email)}`,
        );
        onSubmit(values);
        toast({ status: "success", description: "DSR Link Copied!" });
      }}
      validationSchema={() => {
        return Yup.object().shape({
          identity: Yup.object().shape({
            email: Yup.string().email().required().label("Email Address"),
          }),
        });
      }}
    >
      {({ dirty, isValid }) => {
        return (
          <FormikForm>
            <Stack spacing={6} mb={2}>
              <IdentityFields identityInputs={{ email: "required" }} />
              <div className="flex gap-4 self-end">
                <Button onClick={onCancel}>Cancel</Button>
                <Button
                  htmlType="submit"
                  type="primary"
                  disabled={!dirty || !isValid}
                  data-testid="submit-btn"
                  icon={<LinkIcon />}
                >
                  Copy
                </Button>
              </div>
            </Stack>
          </FormikForm>
        );
      }}
    </Formik>
  );
};

export default SubmitPrivacyRequestForm;
