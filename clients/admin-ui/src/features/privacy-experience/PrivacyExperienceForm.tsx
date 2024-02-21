import {
  ArrowForwardIcon,
  Button,
  Divider,
  Flex,
  Heading,
  Text,
} from "@fidesui/react";
import { useFormikContext } from "formik";
import { useState } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  CustomSelect,
  CustomSwitch,
  // CustomTextArea,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import ScrollableList from "~/features/common/ScrollableList";
import {
  selectAllLanguages,
  selectPage as selectLanguagePage,
  selectPageSize as selectLanguagePageSize,
  useGetAllLanguagesQuery,
} from "~/features/privacy-experience/language.slice";
import {
  selectAllPrivacyNotices,
  selectPage as selectNoticePage,
  selectPageSize as selectNoticePageSize,
  useGetAllPrivacyNoticesQuery,
} from "~/features/privacy-notices/privacy-notices.slice";
import {
  ComponentType,
  ExperienceConfigCreate,
  ExperienceTranslation,
  PrivacyNoticeRegion,
  SupportedLanguage,
} from "~/types/api";

const componentTypeOptions = [
  {
    label: "Banner and modal",
    value: ComponentType.BANNER_AND_MODAL,
  },
  {
    label: "Banner",
    value: ComponentType.MODAL,
  },
];

export const PrivacyExperienceTranslationForm = ({
  name,
}: {
  name: string;
}) => (
  <Flex direction="column" gap={4} w="full">
    <Text>Editing the {name} translation...</Text>
  </Flex>
);

// WIP, don't mind me!

// const PrivacyExperienceTranslationForm = ({
//   name,
//   idx,
//   onSetDefault,
//   onCancel,
// }: {
//   name: string;
//   idx: number;
//   onSetDefault: (index: number) => void;
//   onCancel: () => void;
// }) => {
//   const { values } = useFormikContext<ExperienceConfigCreate>();
//   return (
//     <Flex direction="column" gap={4} w="full">
//       <Button onClick={onCancel}>Back to main form</Button>
//       <Heading fontSize="md" fontWeight="semibold">
//         {name}
//       </Heading>
//       <CustomSwitch
//         name={`translations.${idx}.is_default`}
//         id={`translations.${idx}.is_default`}
//         label="Default language"
//         isDisabled={values.translations![idx].is_default}
//         onChange={() => onSetDefault(idx)}
//         variant="stacked"
//       />
//       <CustomTextInput
//         name={`translations.${idx}.title`}
//         id={`translations.${idx}.title`}
//         label="Title"
//         isRequired
//         variant="stacked"
//       />
//       <CustomTextArea
//         name={`translations.${idx}.description`}
//         id={`translations.${idx}.description`}
//         label="Description"
//         isRequired
//         variant="stacked"
//       />
//       <CustomTextInput
//         name={`translations.${idx}.accept_button_label`}
//         id={`translations.${idx}.accept_button_label`}
//         label={`"Accept" button label`}
//         variant="stacked"
//       />
//       <CustomTextInput
//         name={`translations.${idx}.reject_button_label`}
//         id={`translations.${idx}.reject_button_label`}
//         label={`"Reject" button label`}
//         variant="stacked"
//       />
//       <CustomTextInput
//         name={`translations.${idx}.privacy_preferences_link_label`}
//         id={`translations.${idx}.privacy_preferences_link_label`}
//         label={`"Manage privacy preferences" button label`}
//         variant="stacked"
//       />
//       <CustomTextInput
//         name={`translations.${idx}.save_button_label`}
//         id={`translations.${idx}.save_button_label`}
//         label={`"Save" button label`}
//         variant="stacked"
//       />
//       <CustomTextInput
//         name={`translations.${idx}.acknowledge_button_label`}
//         id={`translations.${idx}.acknowledge_button_label`}
//         label={`"Acknowledge" button label`}
//         variant="stacked"
//       />
//       <CustomTextInput
//         name={`translations.${idx}.privacy_policy_link_label`}
//         id={`translations.${idx}.privacy_policy_link_label`}
//         label="Privacy policy link label"
//         variant="stacked"
//       />
//       <CustomTextInput
//         name={`translations.${idx}.privacy_policy_url`}
//         id={`translations.${idx}.privacy_policy_url`}
//         label="Privacy policy link URL"
//         variant="stacked"
//       />
//     </Flex>
//   );
// };

const PrivacyExperienceForm = ({
  translation,
  onSelectTranslation,
}: {
  translation?: ExperienceTranslation;
  onSelectTranslation: (t: ExperienceTranslation) => void;
}) => {
  const [editingStyle, setEditingStyle] = useState<boolean>(false);
  const { values, setFieldValue } = useFormikContext<ExperienceConfigCreate>();

  const noticePage = useAppSelector(selectNoticePage);
  const noticePageSize = useAppSelector(selectNoticePageSize);
  useGetAllPrivacyNoticesQuery({ page: noticePage, size: noticePageSize });
  const allPrivacyNotices = useAppSelector(selectAllPrivacyNotices);

  const getPrivacyNoticeName = (id: string) => {
    const notice = allPrivacyNotices.find((n) => n.id === id);
    return notice?.name ?? id;
  };

  const allRegions = Object.entries(PrivacyNoticeRegion).map(
    (entry) => entry[1]
  ) as PrivacyNoticeRegion[];

  // const handleSetNewDefaultLanguage = (newDefaultIndex: number) => {
  //   const newTranslations = values.translations!.slice();
  //   newTranslations.find((t) => t.is_default)!.is_default = false;
  //   newTranslations[newDefaultIndex].is_default = true;
  //   setFieldValue("translations", newTranslations, true);
  // };

  const languagePage = useAppSelector(selectLanguagePage);
  const languagePageSize = useAppSelector(selectLanguagePageSize);
  useGetAllLanguagesQuery({ page: languagePage, size: languagePageSize });
  const allLanguages = useAppSelector(selectAllLanguages);

  const getTranslationDisplayName = (t: ExperienceTranslation) => {
    const language = allLanguages.find((lang) => lang.id === t.language);
    const name = language ? language.name : t.language;
    return `${name}${t.is_default ? " (Default)" : ""}`;
  };

  if (translation) {
    return (
      <PrivacyExperienceTranslationForm
        // idx={values.translations!.findIndex(
        //   (translation) => translation.language === translationToEdit.language
        // )}
        name={getTranslationDisplayName(translation)}
        // onSetDefault={handleSetNewDefaultLanguage}
      />
    );
  }

  if (editingStyle) {
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
        options={componentTypeOptions}
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
        canDeleteItem={(item) => !item.is_default}
        allItems={allLanguages.map((lang) => ({
          language: lang.id as SupportedLanguage,
          is_default: false,
        }))}
        getItemLabel={getTranslationDisplayName}
        createNewValue={(opt) => ({
          language: opt.value as SupportedLanguage,
          is_default: false,
        })}
        onRowClick={onSelectTranslation}
        draggable
      />
    </Flex>
  );
};

export default PrivacyExperienceForm;
