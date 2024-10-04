import { Select } from "chakra-react-select";
import ScrollableList from "common/ScrollableList";
import {
  AntButton,
  Box,
  Divider,
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
  LimitedPrivacyNoticeResponseSchema,
  NoticeTranslation,
  PrivacyNoticeCreation,
  PrivacyNoticeRegion,
  PrivacyNoticeResponseWithRegions,
} from "~/types/api";
import type { MinimalPrivacyNotice } from "~/types/api/models/MinimalPrivacyNotice";

import {
  CONSENT_MECHANISM_OPTIONS,
  defaultInitialValues,
  ENFORCEMENT_LEVEL_OPTIONS,
  transformPrivacyNoticeResponseToCreation,
  ValidationSchema,
} from "./form";
import NoticeKeyField from "./NoticeKeyField";
import {
  selectAllPrivacyNotices,
  selectPage as selectNoticePage,
  selectPageSize as selectNoticePageSize,
  useGetAllPrivacyNoticesQuery,
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

  // Query for all privacy notices
  const allPrivacyNotices: LimitedPrivacyNoticeResponseSchema[] =
    useAppSelector(selectAllPrivacyNotices);
  const noticePage = useAppSelector(selectNoticePage);
  const noticePageSize = useAppSelector(selectNoticePageSize);
  useGetAllPrivacyNoticesQuery({ page: noticePage, size: noticePageSize });

  const getPrivacyNoticeName = ({ id }: { id: string; name: string }) => {
    const notice = allPrivacyNotices.find((n) => n.id === id);
    return notice?.name ?? id;
  };

  const isChildNotice = allPrivacyNotices.some((p) =>
    p.children?.some((c) => c.id === passedInPrivacyNotice?.id),
  );

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

  // @ts-ignore
  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={ValidationSchema}
    >
      {({ values, setFieldValue, dirty, isValid, isSubmitting }) => (
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
                  // type has wrong name in OpenAPI.json -- will be resolved by PROD-2746
                  // @ts-ignore
                  regions={passedInPrivacyNotice?.configured_regions}
                  label="Locations where privacy notice is shown to visitors"
                  tooltip="To configure locations, change the privacy experiences where this notice is shown"
                />
                {!isChildNotice && (
                  <ScrollableList<MinimalPrivacyNotice>
                    label="Child notices"
                    addButtonLabel="Add notice children"
                    allItems={allPrivacyNotices.map((n) => ({
                      id: n.id,
                      name: n.name,
                    }))}
                    values={
                      values.children?.map((n) => ({
                        id: n.id,
                        name: n.name,
                      })) ?? []
                    }
                    setValues={(newValue) =>
                      setFieldValue("children", newValue)
                    }
                    idField="id"
                    getItemLabel={getPrivacyNoticeName}
                    draggable
                    maxHeight={100}
                    baseTestId="children"
                  />
                )}
                <Divider />
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
            <div className="flex gap-2">
              <AntButton
                onClick={() => {
                  router.back();
                }}
              >
                Cancel
              </AntButton>
              <AntButton
                htmlType="submit"
                type="primary"
                disabled={isSubmitting || !dirty || !isValid}
                loading={isSubmitting}
                data-testid="save-btn"
              >
                Save
              </AntButton>
            </div>
          </Stack>
        </Form>
      )}
    </Formik>
  );
};

export default PrivacyNoticeForm;
