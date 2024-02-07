import {
  Button,
  ButtonGroup,
  Divider,
  DragHandleIcon,
  Flex,
  List,
  ListItem,
  Text,
} from "@fidesui/react";
import { Formik } from "formik";
import {
  CustomSelect,
  CustomSwitch,
  CustomTextInput,
  Option,
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
import { Reorder, useDragControls } from "framer-motion";
import { useState } from "react";
import PrivacyExperienceLanguageMenu from "~/features/privacy-experience/PrivacyExperienceLanguageMenu";
import ScrollableList from "~/features/common/ScrollableList";

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

const DragItem = ({ label }: { label: string }) => {
  return (
    <Flex
      direction="row"
      p={2}
      gap={2}
      align="center"
      borderY="1px"
      borderColor="gray.400"
      bgColor="white"
    >
      <DragHandleIcon />
      <Text>{label}</Text>
    </Flex>
  );
};

const NewPrivacyExperienceForm = ({ onCancel }: { onCancel: () => void }) => {
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
    ],
  };

  const handleSubmit = (values: NewPrivacyExperience) => {
    console.log("submitting...");
    console.log(values);
    onCancel();
  };

  const testRegionOptions = ["us_va", "gb_wls", "at", "pl"].map((opt) => ({
    label: opt,
    value: opt,
  }));

  const testComponentOptions = enumToOptions(NewComponentType);
  const testNoticeOptions = [
    "Analytics",
    "Essential",
    "Functional",
    "Marketing",
    "Something Else",
    "Another Notice",
    "So Many",
    "Way Too Many Notices",
  ].map((opt) => ({ label: opt, value: opt }));

  const [noticeOptions, setNoticeOptions] =
    useState<Option[]>(testNoticeOptions);

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
            <CustomTextInput
              name="name"
              id="name"
              label="Experience name (internal admin use only)"
              variant="stacked"
            />
            <Text as="h2" fontWeight="600">
              Locations
            </Text>
            <CustomSelect
              name="regions"
              id="regions"
              options={testRegionOptions}
              isMulti
              label="Locations"
              variant="stacked"
            />
            <Text as="h2" fontWeight="600">
              Experience
            </Text>
            <CustomSelect
              name="component"
              id="component"
              options={testComponentOptions}
              label="Set the type of experience to display"
              variant="stacked"
            />
            <CustomSwitch
              name="dismissable"
              id="dismissable"
              label="Overlay is dismissable"
              variant="stacked"
            />
            <Divider />
            <Text as="h2" fontWeight="600">
              Privacy notices
            </Text>
            <ScrollableList
              values={noticeOptions}
              onReorder={setNoticeOptions}
              draggable
            />
            <Button>+ Add privacy notice</Button>
            <Divider />
            <Text as="h2" fontWeight="600">
              Language
            </Text>
            <PrivacyExperienceLanguageMenu translations={values.translations} />
            <CustomSwitch
              name="allow_language_selection"
              id="allow_language_selection"
              label="Allow language selection in overlay"
              variant="stacked"
            />
            <ButtonGroup>
              <Button
                type="submit"
                colorScheme="primary"
                disabled={!dirty || !isValid}
              >
                Save
              </Button>
              <Button onClick={onCancel}>Cancel</Button>
            </ButtonGroup>
          </Flex>
        );
      }}
    </Formik>
  );
};

export default NewPrivacyExperienceForm;
