import {
  ArrowForwardIcon,
  Button,
  Divider,
  Flex,
  Heading,
  Text,
} from "@fidesui/react";
import { useFormikContext } from "formik";
import {
  CustomSelect,
  CustomSwitch,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { enumToOptions } from "~/features/common/helpers";
import {
  ExperienceConfigCreate,
  ExperienceTranslation,
  PrivacyNoticeRegion,
  PrivacyNoticeResponse,
  SupportedLanguage,
} from "~/types/api";
import { useState } from "react";
import ScrollableList from "~/features/common/ScrollableList";
import {
  selectAllPrivacyNotices,
  selectPage as selectNoticePage,
  selectPageSize as selectNoticePageSize,
  useGetAllPrivacyNoticesQuery,
} from "~/features/privacy-notices/privacy-notices.slice";
import { useAppSelector } from "~/app/hooks";
import {
  selectAllLanguages,
  selectPage as selectLanguagePage,
  selectPageSize as selectLanguagePageSize,
  useGetAllLanguagesQuery,
} from "~/features/privacy-experience/language.slice";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";

enum NewComponentType {
  OVERLAY = "overlay",
  PRIVACY_CENTER = "privacy_center",
  BOTH = "both",
}

// export type NewPrivacyExperience = {
//   name?: string;
//   regions: PrivacyNoticeRegion[];
//   component: NewComponentType; // maybe?
//   dismissable: boolean;
//   allow_language_selection: boolean;
//   translations: PrivacyExperienceTranslation[];
//   privacy_notices: PrivacyNoticeResponse[];
// };

// export type PrivacyExperienceTranslation = {
//   language: string;
//   accept_button_label?: string;
//   acknowledge_button_label?: string;
//   banner_description?: string;
//   banner_title?: string;
//   description?: string;
//   privacy_policy_link_label?: string;
//   privacy_policy_url?: string;
//   privacy_preferences_link_label?: string;
//   reject_button_label?: string;
//   save_button_label?: string;
//   title?: string;
//   version?: number;
//   is_default: boolean;
// };

const NewPrivacyExperienceForm = () => {
  const [translationToEdit, setTranslationToEdit] = useState<
    ExperienceTranslation | undefined
  >(undefined);
  const [editingStyle, setEditingStyle] = useState<boolean>(false);
  const { values, setFieldValue } = useFormikContext<ExperienceConfigCreate>();

  const testComponentOptions = enumToOptions(NewComponentType);

  const languagePage = useAppSelector(selectLanguagePage);
  const languagePageSize = useAppSelector(selectLanguagePageSize);
  useGetAllLanguagesQuery({ page: languagePage, size: languagePageSize });
  const allLanguages = useAppSelector(selectAllLanguages);

  const getTranslationLanguageName = (translation: ExperienceTranslation) => {
    const language = allLanguages.find(
      (lang) => lang.id === translation.language
    );
    const name = language ? language.name : translation.language;
    return `${name}` + (translation.is_default ? " (Default)" : "");
  };

  const noticePage = useAppSelector(selectNoticePage);
  const noticePageSize = useAppSelector(selectNoticePageSize);
  useGetAllPrivacyNoticesQuery({ page: noticePage, size: noticePageSize });
  const allPrivacyNotices = useAppSelector(selectAllPrivacyNotices);

  const getPrivacyNoticeName = (id: string) => {
    const notice = allPrivacyNotices.find((notice) => notice.id === id);
    return notice?.name ?? id;
  };

  const allRegions = Object.entries(PrivacyNoticeRegion).map(
    (entry) => entry[1]
  ) as PrivacyNoticeRegion[];

  if (translationToEdit) {
    return (
      <>
        <Button onClick={() => setTranslationToEdit(undefined)}>
          Back to main form
        </Button>
        <Text>
          Editing the {getTranslationLanguageName(translationToEdit)}{" "}
          translation coming soon™
        </Text>
      </>
    );
  } else if (editingStyle) {
    return (
      <>
        <Button onClick={() => setEditingStyle(false)}>
          Back to main form
        </Button>
        <Text>Editing experience style coming soon™</Text>
      </>
    );
  }

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
        isRequired
      />
      <CustomSwitch
        name="dismissable"
        id="dismissable"
        label="Overlay is dismissable"
        variant="stacked"
      />
      <Button
        onClick={() => setEditingStyle(true)}
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
        allItems={allPrivacyNotices.map((n) => n.id)}
        values={values.privacy_notice_ids ?? []}
        setValues={(newValues) =>
          setFieldValue("privacy_notice_ids", newValues)
        }
        getItemLabel={getPrivacyNoticeName}
        draggable
      />
      <Divider />
      <Text as="h2" fontWeight="600">
        Locations & Languages
      </Text>
      <ScrollableList
        label="Locations for this experience"
        addButtonLabel="Add location"
        allItems={allRegions}
        values={values.regions ?? []}
        setValues={(newValues) => setFieldValue("regions", newValues)}
        getItemLabel={(item) => PRIVACY_NOTICE_REGION_RECORD[item]}
        draggable
      />
      <ScrollableList
        label="Languages for this experience"
        addButtonLabel="Add language"
        values={values.translations ?? []}
        setValues={(newValues) => setFieldValue("translations", newValues)}
        idField="language"
        canDeleteItem={(item) => {
          return !item.is_default;
        }}
        allItems={allLanguages.map((lang) => ({
          language: lang.id as SupportedLanguage,
          is_default: false,
        }))}
        getItemLabel={getTranslationLanguageName}
        createNewValue={(opt) => ({
          language: opt.value as SupportedLanguage,
          is_default: false,
        })}
        onRowClick={(item) => setTranslationToEdit(item)}
        draggable
      />
    </Flex>
  );
};

export default NewPrivacyExperienceForm;
