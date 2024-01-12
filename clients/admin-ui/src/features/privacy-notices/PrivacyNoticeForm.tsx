import { Button, ButtonGroup, Stack, useToast } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import FormSection from "~/features/common/form/FormSection";
import {
  CustomSelect,
  CustomSwitch,
  CustomTextInput,
} from "~/features/common/form/inputs";
import {
  enumToOptions,
  getErrorMessage,
  isErrorResult,
} from "~/features/common/helpers";
import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/v2/routes";
import { PRIVACY_NOTICE_REGION_OPTIONS } from "~/features/common/privacy-notice-regions";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  selectEnabledDataUseOptions,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";
import { MECHANISM_MAP } from "~/features/privacy-notices/constants";
import PrivacyNoticeTranslationForm from "~/features/privacy-notices/PrivacyNoticeTranslationForm";
import { ConsentMechanism, PrivacyNoticeCreation } from "~/types/api";

// import ConsentMechanismForm from "./ConsentMechanismForm";
import {
  defaultInitialValues,
  newDefaultInitialValues,
  NewPrivacyNotice,
  // transformPrivacyNoticeResponseToCreation,
  ValidationSchema,
} from "./form";
import NoticeKeyField from "./NoticeKeyField";
import {
  usePatchPrivacyNoticesMutation,
  usePostPrivacyNoticeMutation,
} from "./privacy-notices.slice";

const PrivacyNoticeForm = ({
  privacyNotice: passedInPrivacyNotice,
}: {
  privacyNotice?: NewPrivacyNotice;
}) => {
  const router = useRouter();
  // const toast = useToast();
  // const initialValues = passedInPrivacyNotice
  //   ? transformPrivacyNoticeResponseToCreation(passedInPrivacyNotice)
  //   : defaultInitialValues;

  // Query for data uses
  useGetAllDataUsesQuery();
  const dataUseOptions = useAppSelector(selectEnabledDataUseOptions);

  // const [patchNoticesMutationTrigger] = usePatchPrivacyNoticesMutation();
  // const [postNoticesMutationTrigger] = usePostPrivacyNoticeMutation();

  const isEditing = useMemo(
    () => !!passedInPrivacyNotice,
    [passedInPrivacyNotice]
  );

  const handleSubmit = async (values: NewPrivacyNotice) => {
    const { newLanguage, ...rest } = values;
    console.log("submitting privacy notice...");
    console.log(rest);
    // let result;
    // if (isEditing) {
    //   result = await patchNoticesMutationTrigger([values]);
    // } else {
    //   result = await postNoticesMutationTrigger([values]);
    // }

    // if (isErrorResult(result)) {
    //   toast(errorToastParams(getErrorMessage(result.error)));
    // } else {
    //   toast(
    //     successToastParams(
    //       `Privacy notice ${isEditing ? "updated" : "created"}`
    //     )
    //   );
    //   if (!isEditing) {
    //     router.push(PRIVACY_NOTICES_ROUTE);
    //   }
    // }
  };

  const CONSENT_MECHANISM_OPTIONS = enumToOptions(ConsentMechanism).map(
    (opt) => ({
      label: MECHANISM_MAP.get(opt.label) || opt.label,
      value: opt.value,
    })
  );

  return (
    <Formik
      initialValues={newDefaultInitialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      // validationSchema={ValidationSchema}
    >
      {({ dirty, isValid, isSubmitting }) => (
        <Form>
          <Stack spacing={10}>
            <Stack spacing={6}>
              <FormSection title="Privacy notice details">
                <CustomTextInput
                  // label="Title of the consent notice as displayed to the user"
                  label="Notice title"
                  name="name"
                  variant="stacked"
                />
                <CustomSelect
                  name="consent_mechanism"
                  label="Consent mechanism"
                  options={CONSENT_MECHANISM_OPTIONS}
                  variant="stacked"
                />
                <NoticeKeyField isEditing={isEditing} />
                {passedInPrivacyNotice ? (
                  <CustomSelect
                    name="regions"
                    label="Locations where consent notice is shown to visitors"
                    tooltip="Add locations to this privacy notice by configuring the corresponding privacy experience"
                    options={PRIVACY_NOTICE_REGION_OPTIONS}
                    variant="stacked"
                    placeholder="No locations assigned"
                    isDisabled
                    isMulti
                  />
                ) : null}
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
                {/* <ConsentMechanismForm /> */}
              </FormSection>
              <PrivacyNoticeTranslationForm />
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
