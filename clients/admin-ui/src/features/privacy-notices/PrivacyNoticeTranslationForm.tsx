import {
  AntButton as Button,
  AntSelect as Select,
  AntTabs as Tabs,
  Flex,
  Heading,
  Icons,
} from "fidesui";
import { FieldArray, useFormikContext } from "formik";
import { useState } from "react";

import { useAppSelector } from "~/app/hooks";
import FormSection from "~/features/common/form/FormSection";
import { CustomTextArea, CustomTextInput } from "~/features/common/form/inputs";
import { useGetConfigurationSettingsQuery } from "~/features/config-settings/config-settings.slice";
import {
  selectAllLanguages,
  selectPage,
  selectPageSize,
  useGetAllLanguagesQuery,
} from "~/features/privacy-experience/language.slice";
import { OOBTranslationNotice } from "~/features/privacy-experience/PrivacyExperienceTranslationForm";
import {
  NoticeTranslation,
  PrivacyNoticeCreation,
  SupportedLanguage,
} from "~/types/api";

const NoticeFormFields = ({ index }: { index: number }) => (
  <>
    <CustomTextInput
      autoFocus={index !== 0}
      name={`translations.${index}.title`}
      label="Title of privacy notice as displayed to user"
      variant="stacked"
    />
    <CustomTextArea
      name={`translations.${index}.description`}
      label="Privacy notice displayed to the user"
      variant="stacked"
    />
  </>
);

const AddTranslationMenu = ({
  languageOptions,
  handleCreateLanguage,
}: {
  languageOptions: { label: string; value: string }[];
  handleCreateLanguage: (language: SupportedLanguage) => void;
}) => {
  const [isSelectingLanguage, setIsSelectingLanguage] = useState(false);

  const handleSelect = (language: SupportedLanguage) => {
    handleCreateLanguage(language as SupportedLanguage);
    setIsSelectingLanguage(false);
  };

  if (isSelectingLanguage) {
    return (
      <Select
        autoFocus
        defaultOpen
        allowClear
        placeholder="Select a language..."
        options={languageOptions}
        onChange={handleSelect}
        data-testid="select-language"
        className="w-full"
      />
    );
  }

  return (
    <Button
      block
      icon={<Icons.Add />}
      iconPosition="end"
      onClick={() => setIsSelectingLanguage(true)}
      data-testid="add-language-btn"
      className="mb-1"
    >
      Add
    </Button>
  );
};

const TranslationFormBlock = ({
  index,
  name,
  isOOB,
}: {
  index: number;
  name: string;
  isOOB?: boolean;
}) => (
  <Flex direction="column" gap={6}>
    <Heading size="sm">Edit {name} translation</Heading>
    {isOOB ? <OOBTranslationNotice languageName={name} /> : null}
    <NoticeFormFields index={index} />
  </Flex>
);

const PrivacyNoticeTranslationForm = ({
  availableTranslations,
}: {
  availableTranslations?: NoticeTranslation[];
}) => {
  const { values, setFieldValue } = useFormikContext<PrivacyNoticeCreation>();

  const [translationIsOOB, setTranslationIsOOB] = useState<boolean>(false);
  const [activeLanguage, setActiveLanguage] = useState<string>(
    values.translations?.[0]?.language ?? "",
  );

  const { data: appConfig } = useGetConfigurationSettingsQuery({
    api_set: false,
  });
  const translationsEnabled =
    appConfig?.plus_consent_settings?.enable_translations;

  const languagePage = useAppSelector(selectPage);
  const languagePageSize = useAppSelector(selectPageSize);
  useGetAllLanguagesQuery({ page: languagePage, size: languagePageSize });
  const allLanguages = useAppSelector(selectAllLanguages)
    .slice()
    .sort((a, b) => a.name.localeCompare(b.name));

  const languageOptions = allLanguages
    .filter((lang) =>
      values.translations?.every(
        (translation) => translation.language !== lang.id,
      ),
    )
    .map((lang) => ({ label: lang.name, value: lang.id as SupportedLanguage }));

  const handleTabSelected = (language: string) => {
    setActiveLanguage(language);
    setTranslationIsOOB(false);
  };

  const handleCreateLanguage = (language: SupportedLanguage) => {
    const availableTranslation = availableTranslations?.find(
      (translation) => translation.language === language,
    );
    setTranslationIsOOB(!!availableTranslation);
    const newTranslation = availableTranslation ?? {
      language: language as SupportedLanguage,
      title: "",
      description: "",
    };
    setActiveLanguage(language);
    setFieldValue("translations", [...values.translations!, newTranslation]);
  };

  const handleLanguageDeleted = (language: string) => {
    const newTranslations = values.translations
      ? values.translations.slice().filter((lang) => lang.language !== language)
      : [];
    const newActiveLanguage =
      activeLanguage === language
        ? (newTranslations[newTranslations.length - 1]?.language ?? "")
        : activeLanguage;
    setFieldValue("translations", newTranslations);
    setActiveLanguage(newActiveLanguage);
  };

  const getLanguageDisplayName = (lang: SupportedLanguage) =>
    allLanguages.find((language) => language.id === lang)?.name ?? lang;

  if (!translationsEnabled) {
    return (
      <FormSection title="Notice text">
        <NoticeFormFields index={0} />
      </FormSection>
    );
  }

  return (
    <FormSection title="Localizations">
      <FieldArray
        name="translations"
        render={() => (
          <Tabs
            activeKey={activeLanguage}
            onChange={handleTabSelected}
            type="editable-card"
            tabBarExtraContent={
              !!languageOptions.length && (
                <AddTranslationMenu
                  languageOptions={languageOptions}
                  handleCreateLanguage={handleCreateLanguage}
                />
              )
            }
            hideAdd
            onEdit={(e, action) => {
              if (action === "remove") {
                handleLanguageDeleted(e as SupportedLanguage);
              }
            }}
            items={values.translations!.map((translation) => ({
              key: translation.language,
              label: getLanguageDisplayName(translation.language),
              children: (
                <TranslationFormBlock
                  index={values.translations!.findIndex(
                    (t) => t.language === translation.language,
                  )}
                  name={getLanguageDisplayName(translation.language)}
                  isOOB={translationIsOOB}
                />
              ),
              closable: values.translations!.length > 1,
            }))}
          />
        )}
      />
    </FormSection>
  );
};

export default PrivacyNoticeTranslationForm;
