import { Select } from "chakra-react-select";
import {
  Box,
  Button,
  ButtonGroup,
  Flex,
  FormLabel,
  Stack,
  useToast,
  VStack,
} from "fidesui";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import FormSection from "~/features/common/form/FormSection";
import {
  CustomSelect,
  CustomSwitch,
  CustomTextInput,
  SELECT_STYLES,
} from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/v2/routes";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  selectEnabledDataUseOptions,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";
import PrivacyNoticeTranslationForm from "~/features/privacy-notices/PrivacyNoticeTranslationForm";
import {
  NoticeTranslation,
  PrivacyNoticeCreation,
  PrivacyNoticeRegion,
  PrivacyNoticeResponseWithRegions,
} from "~/types/api";

import {
  CONSENT_MECHANISM_OPTIONS,
  defaultInitialValues,
  ENFORCEMENT_LEVEL_OPTIONS,
  transformPrivacyNoticeResponseToCreation,
  ValidationSchema,
} from "./form";
import NoticeKeyField from "./NoticeKeyField";
import {
  usePatchPrivacyNoticesMutation,
  usePostPrivacyNoticeMutation,
} from "./privacy-notices.slice";

const PrivacyNoticeLocationDisplay = ({
  regions,
  label,
  tooltip,
}: {
  regions?: PrivacyNoticeRegion[];
  label: string;
  tooltip: string;
}) => (
  <VStack align="start">
    <Flex align="start">
      {label ? (
        <FormLabel htmlFor="regions" fontSize="xs" my={0} mr={1}>
          {label}
        </FormLabel>
      ) : null}
      {tooltip ? <QuestionTooltip label={tooltip} /> : null}
    </Flex>
    <Box w="100%" data-testid="notice-locations">
      <Select
        chakraStyles={{
          ...SELECT_STYLES,
          dropdownIndicator: (provided) => ({
            ...provided,
            display: "none",
          }),
          multiValueRemove: (provided) => ({
            ...provided,
            display: "none",
          }),
        }}
        classNamePrefix="notice-locations"
        size="sm"
        isMulti
        isDisabled
        placeholder="No locations assigned"
        value={
          regions?.map((r) => ({
            label: PRIVACY_NOTICE_REGION_RECORD[r],
            value: r,
          })) ?? []
        }
      />
    </Box>
  </VStack>
);

const PrivacyNoticeForm = ({
  privacyNotice: passedInPrivacyNotice,
  availableTranslations,
}: {
  privacyNotice?: PrivacyNoticeResponseWithRegions;
  availableTranslations?: NoticeTranslation[];
}) => {
  const router = useRouter();
  const toast = useToast();
  const initialValues = passedInPrivacyNotice
    ? transformPrivacyNoticeResponseToCreation(passedInPrivacyNotice)
    : defaultInitialValues;

  // Query for data uses
  useGetAllDataUsesQuery();
  const dataUseOptions = useAppSelector(selectEnabledDataUseOptions);

  const [patchNoticesMutationTrigger] = usePatchPrivacyNoticesMutation();
  const [postNoticesMutationTrigger] = usePostPrivacyNoticeMutation();

  const isEditing = useMemo(
    () => !!passedInPrivacyNotice,
    [passedInPrivacyNotice],
  );

  const handleSubmit = async (values: PrivacyNoticeCreation) => {
    let result;
    if (isEditing) {
      const valuesToSubmit = {
        ...values,
        id: passedInPrivacyNotice!.id,
        translations: values.translations ?? [],
      };
      result = await patchNoticesMutationTrigger(valuesToSubmit);
    } else {
      result = await postNoticesMutationTrigger(values);
    }

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          `Privacy notice ${isEditing ? "updated" : "created"}`,
        ),
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
                  label="Notice title"
                  name="name"
                  isRequired
                  variant="stacked"
                />
                <CustomSelect
                  name="consent_mechanism"
                  label="Consent mechanism"
                  options={CONSENT_MECHANISM_OPTIONS}
                  isRequired
                  variant="stacked"
                />
                <NoticeKeyField isEditing={isEditing} />
                <PrivacyNoticeLocationDisplay
                  regions={passedInPrivacyNotice?.configured_regions}
                  label="Locations where privacy notice is shown to visitors"
                  tooltip="To configure locations, change the privacy experiences where this notice is shown"
                />
                <CustomSwitch
                  name="has_gpc_flag"
                  label="Configure whether this notice conforms to the Global Privacy Control"
                  variant="stacked"
                />
                <CustomSelect
                  name="data_uses"
                  label="Data use"
                  options={dataUseOptions}
                  isMulti
                  variant="stacked"
                />
                <CustomSelect
                  name="enforcement_level"
                  label="Enforcement level"
                  options={ENFORCEMENT_LEVEL_OPTIONS}
                  isRequired
                  variant="stacked"
                />
              </FormSection>
              <PrivacyNoticeTranslationForm
                availableTranslations={availableTranslations}
              />
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
