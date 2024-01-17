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
import {
  ConsentMechanism,
  EnforcementLevel,
  PrivacyNoticeCreation,
  PrivacyNoticeRegion,
} from "~/types/api";

const DUMMY_NOTICE = {
  id: "pri_9bfcbf0a-6417-4778-9ce2-9bcdd8317452",
  created_at: "2024-01-04T21:56:23.656562+00:00",
  updated_at: "2024-01-04T21:57:35.009637+00:00",
  name: "Data Sales and Sharing",
  consent_mechanism: "opt_out" as ConsentMechanism,
  notice_key: "data_sales_and_sharing",
  regions: [
    "us_co",
    "us_ct",
    "us_ia",
    "us_ut",
    "us_va",
  ] as PrivacyNoticeRegion[],
  data_uses: [
    "marketing.advertising.first_party.targeted",
    "marketing.advertising.third_party.targeted",
  ],
  enforcement_level: "system_wide" as EnforcementLevel,
  has_gpc_flag: true,
  disabled: false,
  internal_description:
    "“Sale of personal“ data means the exchange of personal data for monetary or other valuable consideration. Data sharing refers to sharing of data with third parties for the purpose of cross contextual behavioral advertising. This is also closely analogous to “Targeted Advertising” as defined in other U.S. state laws and they have been combined here under one notice.",
  origin: "pri_309d287c-b208-4fd1-93b2-7b2ff13eddat",
  default_preference: "opt_in",
  systems_applicable: true,
  cookies: [],
  translations: [
    {
      language: "en-US",
      title: "Data Sales and Sharing",
      description:
        "We may transfer or share your personal information to third parties in exchange for monetary or other valuable consideration or for the purposes of cross-contextual targeted advertising. You can learn more about what information is used for this purpose in our privacy notice.",
      privacy_notice_history_id: "pri_da253ad5-c870-495a-b1b5-19de864c0616",
    },
  ],
};

// import ConsentMechanismForm from "./ConsentMechanismForm";
import {
  defaultInitialValues,
  newDefaultInitialValues,
  NewPrivacyNotice,
  transformNewPrivacyNoticeResponseToCreation,
  transformPrivacyNoticeResponseToCreation,
  ValidationSchema,
} from "./form";
import NoticeKeyField from "./NoticeKeyField";
import {
  usePatchPrivacyNoticesMutation,
  usePostPrivacyNoticeMutation,
} from "./privacy-notices.slice";

const PrivacyNoticeForm = () =>
  // {
  //   privacyNotice: passedInPrivacyNotice,
  // }: {
  //   privacyNotice?: NewPrivacyNotice;
  // }
  {
    // const passedInPrivacyNotice = DUMMY_NOTICE;
    const passedInPrivacyNotice: NewPrivacyNotice | undefined = undefined;

    const router = useRouter();
    // const toast = useToast();
    const initialValues = passedInPrivacyNotice
      ? transformNewPrivacyNoticeResponseToCreation(passedInPrivacyNotice)
      : newDefaultInitialValues;

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
        initialValues={initialValues}
        enableReinitialize
        onSubmit={handleSubmit}
        // validationSchema={ValidationSchema}
      >
        {({ values, dirty, isValid, isSubmitting }) => {
          console.log(values);
          return (
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
          );
        }}
      </Formik>
    );
  };

export default PrivacyNoticeForm;
