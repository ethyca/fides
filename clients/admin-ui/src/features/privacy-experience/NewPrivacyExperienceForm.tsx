import {
  ArrowForwardIcon,
  Button,
  Divider,
  Flex,
  Heading,
  Text,
} from "@fidesui/react";
import { Formik } from "formik";
import {
  CustomSelect,
  CustomSwitch,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { enumToOptions } from "~/features/common/helpers";
import {
  BannerEnabled,
  ConsentMechanism,
  EnforcementLevel,
  PrivacyNoticeRegion,
  PrivacyNoticeResponse,
  UserConsentPreference,
} from "~/types/api";
import { useState } from "react";
import ScrollableList from "~/features/common/ScrollableList";

import localeCodes, { ILocale } from "locale-codes";
import {
  selectAllPrivacyNotices,
  useGetAllPrivacyNoticesQuery,
} from "~/features/privacy-notices/privacy-notices.slice";
import { useAppSelector } from "~/app/hooks";

enum NewComponentType {
  OVERLAY = "overlay",
  PRIVACY_CENTER = "privacy_center",
  BOTH = "both",
}

export type NewPrivacyExperience = {
  name?: string;
  regions: PrivacyNoticeRegion[];
  component: NewComponentType; // maybe?
  dismissable: boolean;
  allow_language_selection: boolean;
  translations: PrivacyExperienceTranslation[];
  privacy_notices: PrivacyNoticeResponse[];
};

export type PrivacyExperienceTranslation = {
  language: string;
  accept_button_label?: string;
  acknowledge_button_label?: string;
  banner_description?: string;
  banner_enabled?: BannerEnabled;
  banner_title?: string;
  description?: string;
  privacy_policy_link_label?: string;
  privacy_policy_url?: string;
  privacy_preferences_link_label?: string;
  reject_button_label?: string;
  save_button_label?: string;
  title?: string;
  version?: number;
  is_default: boolean;
};

const NewPrivacyExperienceForm = () => {
  const defaultInitialValues: NewPrivacyExperience = {
    regions: [],
    component: NewComponentType.OVERLAY,
    dismissable: false,
    allow_language_selection: true,
    privacy_notices: [],
    translations: [
      {
        language: "en-US",
        version: 1,
        is_default: true,
      },
    ],
  };

  const initialValues: NewPrivacyExperience = {
    // id: "pri_exp_sfasdf_sf",
    regions: [
      "us_va",
      "gb_wls",
      "at",
      "pl",
      "nl",
      "us_ut",
      "us_ca",
    ] as PrivacyNoticeRegion[],
    component: NewComponentType.OVERLAY,
    dismissable: true,
    allow_language_selection: true,
    translations: [
      {
        // id: "pri_sdafsf",
        language: "en",
        accept_button_label: "Opt in to all",
        acknowledge_button_label: "OK",
        description:
          "We use cookies and similar methods to recognize visitors and remember their preferences. We may also use them to measure ad campaign effectiveness, target ads, and analyze site traffic. Depending on your location, you may opt-in or opt out of the use of these technologies.",
        privacy_policy_link_label: "Privacy Policy",
        privacy_preferences_link_label: "Manage preferences",
        reject_button_label: "Opt out of all",
        save_button_label: "Save",
        title: "Manage your consent preferences",
        version: 1,
        is_default: true,
        // experience_config_history_id:
        //   "pri_e1d88e37-54fe-41f1-904c-fd3c87884b4b",
      },
    ],
    // created_at: "2024-01-04T21:56:23.600884+00:00",
    // updated_at: "2024-01-04T21:56:23.600884+00:00",
    privacy_notices: [
      {
        id: "pri_9bfcbf0a-6417-4778-9ce2-9bcdd8317452",
        created_at: "2024-01-04T21:56:23.656562+00:00",
        updated_at: "2024-01-04T21:57:35.009637+00:00",
        name: "Data Sales and Sharing",
        consent_mechanism: ConsentMechanism.OPT_OUT,
        data_uses: [
          "marketing.advertising.first_party.targeted",
          "marketing.advertising.third_party.targeted",
        ],
        disabled: false,
        enforcement_level: EnforcementLevel.SYSTEM_WIDE,
        has_gpc_flag: true,
        internal_description:
          "“Sale of personal“ data means the exchange of personal data for monetary or other valuable consideration. Data sharing refers to sharing of data with third parties for the purpose of cross contextual behavioral advertising. This is also closely analogous to “Targeted Advertising” as defined in other U.S. state laws and they have been combined here under one notice.",
        notice_key: "data_sales_and_sharing",
        origin: "pri_309d287c-b208-4fd1-93b2-7b2ff13eddat",
        default_preference: UserConsentPreference.OPT_IN,
        systems_applicable: true,
        cookies: [],
        version: 1,
        privacy_notice_history_id: "test",
        // translations: [
        //   {
        //     id: "pri_sdafsf",
        //     language: "en",
        //     title: "Data Sales and Sharing",
        //     description:
        //       "We may transfer or share your personal information to third parties in exchange for monetary or other valuable consideration or for the purposes of cross-contextual targeted advertising. You can learn more about what information is used for this purpose in our privacy notice.",
        //     version: 3,
        //     privacy_notice_history_id:
        //       "pri_da253ad5-c870-495a-b1b5-19de864c0616",
        //   },
        // ],
      },
      {
        id: "pri_9bfcbf0a-6417-4778-9ce2-9bcdd8317453",
        created_at: "2024-01-04T21:56:23.656562+00:00",
        updated_at: "2024-01-04T21:57:35.009637+00:00",
        name: "Another Data Sales and Sharing",
        consent_mechanism: ConsentMechanism.OPT_OUT,
        data_uses: [
          "marketing.advertising.first_party.targeted",
          "marketing.advertising.third_party.targeted",
        ],
        disabled: false,
        enforcement_level: EnforcementLevel.SYSTEM_WIDE,
        has_gpc_flag: true,
        internal_description:
          "“Sale of personal“ data means the exchange of personal data for monetary or other valuable consideration. Data sharing refers to sharing of data with third parties for the purpose of cross contextual behavioral advertising. This is also closely analogous to “Targeted Advertising” as defined in other U.S. state laws and they have been combined here under one notice.",
        notice_key: "data_sales_and_sharing",
        origin: "pri_309d287c-b208-4fd1-93b2-7b2ff13eddat",
        default_preference: UserConsentPreference.OPT_IN,
        systems_applicable: true,
        cookies: [],
        version: 1,
        privacy_notice_history_id: "test",
        // translations: [
        //   {
        //     id: "pri_sdafsf",
        //     language: "en",
        //     title: "Data Sales and Sharing",
        //     description:
        //       "We may transfer or share your personal information to third parties in exchange for monetary or other valuable consideration or for the purposes of cross-contextual targeted advertising. You can learn more about what information is used for this purpose in our privacy notice.",
        //     version: 3,
        //     privacy_notice_history_id:
        //       "pri_da253ad5-c870-495a-b1b5-19de864c0616",
        //   },
        // ],
      },
    ],
  };

  const handleSubmit = (values: NewPrivacyExperience) => {
    console.log("submitting...");
    console.log(values);
  };

  const testComponentOptions = enumToOptions(NewComponentType);

  // TEMP
  // const getLanguageOption = (locale: ILocale) => {
  //   return {
  //     label: locale.location
  //       ? `${locale.name} (${locale.location})`
  //       : locale.name,
  //     value: locale.tag,
  //   };
  // };

  const getLanguageDisplayName = (locale: ILocale) => {
    return locale.location
      ? `${locale.name} (${locale.location})`
      : locale.name;
  };

  // const [noticeOptions, setNoticeOptions] = useState<Option[]>([]);
  const [notices, setNotices] = useState<PrivacyNoticeResponse[]>([]);
  const [regions, setRegions] = useState<PrivacyNoticeRegion[]>([]);
  const [languages, setLanguages] = useState<PrivacyExperienceTranslation[]>(
    []
  );

  return (
    <Formik
      initialValues={defaultInitialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      // validationSchema={validationSchema}
    >
      {({ dirty, values, isValid }) => {
        return (
          <Flex direction="column" gap={4} w="full">
            <Heading fontSize="md" fontWeight="semibold">
              Configure experience
            </Heading>
            <CustomTextInput
              name="name"
              id="name"
              label="Name (internal admin use only)"
              variant="stacked"
            />
            <CustomSelect
              name="component"
              id="component"
              options={testComponentOptions}
              label="Experience Type"
              variant="stacked"
            />
            <CustomSwitch
              name="dismissable"
              id="dismissable"
              label="Overlay is dismissable"
              variant="stacked"
            />
            <Button
              size="sm"
              variant="outline"
              rightIcon={<ArrowForwardIcon />}
            >
              Customize appearance
            </Button>
            <Divider />
            <Heading fontSize="md" fontWeight="semibold">
              Privacy notices
            </Heading>
            <ScrollableList
              addButtonLabel="Add privacy notice"
              allItems={initialValues.privacy_notices}
              values={notices}
              setValues={setNotices}
              idField="id"
              nameField="name"
              draggable
            />
            <Divider />
            <Text as="h2" fontWeight="600">
              Locations & Languages
            </Text>
            <ScrollableList
              label="Locations for this experience"
              addButtonLabel="Add location"
              allItems={initialValues.regions}
              values={regions}
              setValues={setRegions}
              draggable
            />
            <ScrollableList
              label="Languages for this experience"
              addButtonLabel="Add language"
              values={languages}
              setValues={setLanguages}
              idField="language"
              allItems={localeCodes.all.map((locale) => ({
                language: locale.tag,
                is_default: false,
              }))}
              getItemLabel={(translation) =>
                getLanguageDisplayName(
                  localeCodes.getByTag(translation.language)
                )
              }
              createNewValue={(opt) => ({
                language: opt.value,
                is_default: false,
              })}
              draggable
            />
          </Flex>
        );
      }}
    </Formik>
  );
};

export default NewPrivacyExperienceForm;
