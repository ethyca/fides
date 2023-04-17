import {
  Box,
  Button,
  ButtonGroup,
  HStack,
  Stack,
  Text,
  useToast,
} from "@fidesui/react";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";

import { useAppSelector } from "~/app/hooks";
import FormSection from "~/features/common/form/FormSection";
import {
  CustomSelect,
  CustomSwitch,
  CustomTextArea,
  CustomTextInput,
} from "~/features/common/form/inputs";
import {
  enumToOptions,
  getErrorMessage,
  isErrorResult,
} from "~/features/common/helpers";
import {
  selectDataUseOptions,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";
import {
  ConsentMechanism,
  EnforcementLevel,
  PrivacyNoticeCreation,
  PrivacyNoticeRegion,
  PrivacyNoticeResponse,
} from "~/types/api";

import { errorToastParams, successToastParams } from "../common/toast";
import { MECHANISM_MAP } from "./constants";
import {
  defaultInitialValues,
  transformPrivacyNoticeResponseToCreation,
  ValidationSchema,
} from "./form";
import { usePatchPrivacyNoticesMutation } from "./privacy-notices.slice";

const CONSENT_MECHANISM_OPTIONS = enumToOptions(ConsentMechanism).map(
  (opt) => ({
    label: MECHANISM_MAP.get(opt.label) || opt.label,
    value: opt.value,
  })
);

const ENFORCEMENT_OPTIONS = enumToOptions(EnforcementLevel);

const REGION_OPTIONS = enumToOptions(PrivacyNoticeRegion);

const PrivacyNoticeForm = ({
  privacyNotice: passedInPrivacyNotice,
}: {
  privacyNotice?: PrivacyNoticeResponse;
}) => {
  const router = useRouter();
  const toast = useToast();
  const initialValues = passedInPrivacyNotice
    ? transformPrivacyNoticeResponseToCreation(passedInPrivacyNotice)
    : defaultInitialValues;

  // Query for data uses
  useGetAllDataUsesQuery();
  const dataUseOptions = useAppSelector(selectDataUseOptions);

  const [patchNoticesMutationTrigger] = usePatchPrivacyNoticesMutation();

  const handleSubmit = async (values: PrivacyNoticeCreation) => {
    const result = await patchNoticesMutationTrigger([values]);
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(successToastParams("Privacy notice updated"));
    }
  };

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={ValidationSchema}
    >
      {({ dirty, isValid, isSubmitting }) => (
        <Form>
          <Stack spacing={10}>
            <Stack spacing={6}>
              <FormSection title="Privacy notice details">
                <CustomTextInput
                  label="Title of the consent notice as displayed to the user"
                  name="name"
                  variant="stacked"
                />
                <CustomTextArea
                  label="Privacy notice displayed to the user"
                  name="description"
                  variant="stacked"
                />
              </FormSection>
              <FormSection title="Consent mechanism">
                <CustomSelect
                  label="If this use of data requires consent, you can specify the method of consent here."
                  name="consent_mechanism"
                  options={CONSENT_MECHANISM_OPTIONS}
                  variant="stacked"
                />
                <CustomSelect
                  label="Select the enforcement level for this consent mechanism"
                  name="enforcement_level"
                  options={ENFORCEMENT_OPTIONS}
                  variant="stacked"
                />
                <Box>
                  <Text fontSize="sm" fontWeight="medium" mb={2}>
                    Configure whether this notice conforms to the Global Privacy
                    Control.
                  </Text>
                  <CustomSwitch
                    label="GPC Enabled"
                    name="has_gpc_flag"
                    variant="condensed"
                  />
                </Box>
              </FormSection>
              <FormSection title="Privacy notice configuration">
                <CustomSelect
                  name="data_uses"
                  label="Data uses associated with this privacy notice"
                  options={dataUseOptions}
                  variant="stacked"
                  isMulti
                />
                <CustomTextArea
                  label="Description of the privacy notice (visible to internal users only)"
                  name="internal_description"
                  variant="stacked"
                />
                <CustomSelect
                  name="regions"
                  label="Locations where consent notice is shown to visitors"
                  options={REGION_OPTIONS}
                  variant="stacked"
                  isMulti
                />
                <Box>
                  <Text fontSize="sm" fontWeight="medium" mb={2}>
                    Configure the user experience for how this notice is
                    displayed
                  </Text>
                  <HStack justifyContent="space-between">
                    <CustomSwitch
                      label="Show in Privacy Preference Center"
                      name="displayed_in_privacy_center"
                      variant="condensed"
                    />
                    <CustomSwitch
                      label="Show in Banner"
                      name="displayed_in_api"
                      variant="condensed"
                    />
                    <CustomSwitch
                      label="Show in Privacy Modal"
                      name="displayed_in_overlay"
                      variant="condensed"
                    />
                  </HStack>
                </Box>
              </FormSection>
            </Stack>
            <ButtonGroup size="sm" spacing={2}>
              <Button
                variant="outline"
                onClick={() => {
                  router.back();
                }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isDisabled={isSubmitting || !dirty || !isValid}
                isLoading={isSubmitting}
                data-testid="save-btn"
              >
                Save
              </Button>
            </ButtonGroup>
          </Stack>
        </Form>
      )}
    </Formik>
  );
};

export default PrivacyNoticeForm;
