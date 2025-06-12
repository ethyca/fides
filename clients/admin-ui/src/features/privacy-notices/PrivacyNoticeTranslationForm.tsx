import {
  AntButton as Button,
  AntSelect as Select,
  AntTabs as Tabs,
  Box,
  DeleteIcon,
  Flex,
  Heading,
  SmallAddIcon,
  VStack,
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
  NoticeTranslationCreate,
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

const TranslationTabButton = ({
  translation,
  name,
  onLanguageDeleted,
  isActive,
  onClick,
}: {
  translation: NoticeTranslationCreate;
  name: string;
  onLanguageDeleted?: (language: string) => void;
  isActive?: boolean;
  onClick?: () => void;
}) => (
  <Flex gap={2} direction="row" w="100%">
    <Button
      onClick={onClick}
      key={translation.language}
      className={`grow overflow-hidden text-ellipsis whitespace-nowrap border-gray-300 ${isActive ? "bg-gray-500 text-white" : ""}`}
    >
      {name}
    </Button>
    {onLanguageDeleted && (
      <Button
        aria-label="Delete translation"
        onClick={() => onLanguageDeleted(translation.language)}
        icon={<DeleteIcon boxSize={3} />}
        className="min-w-4"
      />
    )}
  </Flex>
);

const PrivacyNoticeTranslationForm = ({
  availableTranslations,
}: {
  availableTranslations?: NoticeTranslation[];
}) => {
  const { values, setFieldValue } = useFormikContext<PrivacyNoticeCreation>();

  const [isSelectingLanguage, setIsSelectingLanguage] =
    useState<boolean>(false);
  const [translationIsOOB, setTranslationIsOOB] = useState<boolean>(false);
  const [tabIndex, setTabIndex] = useState<number>(0);

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

  const handleTabSelected = (index: number) => {
    setTabIndex(index);
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
    setTabIndex(values.translations!.length);
    setFieldValue("translations", [...values.translations!, newTranslation]);
    setIsSelectingLanguage(false);
  };

  const handleLanguageDeleted = (tag: string) => {
    const newTranslations = values.translations
      ? values.translations.slice().filter((lang) => lang.language !== tag)
      : [];
    const newTabIndex =
      tabIndex === newTranslations.length
        ? newTranslations.length - 1
        : tabIndex;
    setFieldValue("translations", newTranslations);
    setTabIndex(newTabIndex);
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
      <Flex gap={8} align="start" w="100%">
        <VStack spacing={4} minW="30%" p={2}>
          <VStack
            spacing={2}
            w="100%"
            p={4}
            maxH={60}
            overflow="scroll"
            outline="1px solid"
            outlineColor="gray.200"
            borderRadius="md"
          >
            {values.translations!.map((translation, idx) => (
              <TranslationTabButton
                translation={translation}
                key={translation.language}
                name={getLanguageDisplayName(translation.language)}
                onLanguageDeleted={handleLanguageDeleted}
                isActive={idx === tabIndex}
                onClick={() => handleTabSelected(idx)}
              />
            ))}
          </VStack>
          {isSelectingLanguage && (
            <Select
              autoFocus
              defaultOpen
              allowClear
              placeholder="Select a language..."
              options={languageOptions}
              onChange={handleCreateLanguage}
              data-testid="select-language"
              className="w-full"
            />
          )}
          {!isSelectingLanguage && !!languageOptions.length && (
            <Button
              icon={<SmallAddIcon boxSize={6} />}
              onClick={() => setIsSelectingLanguage(true)}
              data-testid="add-language-btn"
              className="w-full"
            >
              Add a language
            </Button>
          )}
        </VStack>
        <Box w="100%">
          <FieldArray
            name="translations"
            render={() => (
              <Tabs
                activeKey={tabIndex.toString()}
                onChange={(key) => handleTabSelected(parseInt(key, 10))}
                items={values.translations!.map((translation, idx) => ({
                  key: idx.toString(),
                  label: getLanguageDisplayName(translation.language),
                  children: (
                    <TranslationFormBlock
                      index={idx}
                      name={getLanguageDisplayName(translation.language)}
                      isOOB={translationIsOOB}
                    />
                  ),
                }))}
                // @ts-ignore -- Ant requires a tab bar but we want to skip it
                renderTabBar={() => null}
              />
            )}
          />
        </Box>
      </Flex>
    </FormSection>
  );
};

export default PrivacyNoticeTranslationForm;
