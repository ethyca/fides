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
import { useMemo } from "react";

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
import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/v2/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  selectDataUseOptions,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";
import {
  PrivacyNoticeCreation,
  PrivacyNoticeRegion,
  PrivacyNoticeResponse,
} from "~/types/api";

import ConsentMechanismForm from "./ConsentMechanismForm";
import {
  defaultInitialValues,
  transformPrivacyNoticeResponseToCreation,
  ValidationSchema,
} from "./form";
import {
  usePatchPrivacyNoticesMutation,
  usePostPrivacyNoticeMutation,
} from "./privacy-notices.slice";

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
  const [postNoticesMutationTrigger] = usePostPrivacyNoticeMutation();

  const isEditing = useMemo(
    () => !!passedInPrivacyNotice,
    [passedInPrivacyNotice]
  );

  const handleSubmit = async (values: PrivacyNoticeCreation) => {
    let result;
    if (isEditing) {
      result = await patchNoticesMutationTrigger([values]);
    } else {
      result = await postNoticesMutationTrigger([values]);
    }

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          `Privacy notice ${isEditing ? "updated" : "created"}`
        )
      );
      if (!isEditing) {
        router.push(PRIVACY_NOTICES_ROUTE);
      }
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
              <ConsentMechanismForm />
              <FormSection title="Privacy notice configuration">
                <CustomSelect
                  name="data_uses"
                  label="Data uses associated with this privacy notice"
                  options={dataUseOptions}
                  variant="stacked"
                  isMulti
                  isRequired
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
                  isRequired
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
                      label="API Only"
                      name="displayed_in_api"
                      variant="condensed"
                    />
                    <CustomSwitch
                      label="Show in Privacy Overlay"
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
