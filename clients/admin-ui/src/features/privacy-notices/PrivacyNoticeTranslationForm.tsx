import {
  Button,
  Card,
  Flex,
  Form,
  FormInstance,
  Icons,
  Input,
  Select,
  Tabs,
  Typography,
} from "fidesui";
import { useState } from "react";

import { useAppSelector } from "~/app/hooks";
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

const { Title } = Typography;

const NoticeFormFields = ({ index }: { index: number }) => (
  <>
    <Form.Item
      name={["translations", index, "title"]}
      label="Title of privacy notice as displayed to user"
    >
      <Input
        autoFocus={index !== 0}
        data-testid={`input-translations.${index}.title`}
      />
    </Form.Item>
    <Form.Item
      name={["translations", index, "description"]}
      label="Privacy notice displayed to the user"
    >
      <Input.TextArea data-testid={`input-translations.${index}.description`} />
    </Form.Item>
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
    handleCreateLanguage(language);
    setIsSelectingLanguage(false);
  };

  if (isSelectingLanguage) {
    return (
      <Select
        autoFocus
        defaultOpen
        allowClear
        placeholder="Select a language..."
        aria-label="Select a language"
        options={languageOptions}
        onChange={handleSelect}
        data-testid="select-language"
        className="w-full"
        optionFilterProp="label"
      />
    );
  }

  return (
    <Button
      block
      icon={<Icons.Add />}
      iconPlacement="end"
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
  <Flex vertical gap="middle">
    <Title level={5}>Edit {name} translation</Title>
    {isOOB ? <OOBTranslationNotice languageName={name} /> : null}
    <NoticeFormFields index={index} />
  </Flex>
);

const PrivacyNoticeTranslationForm = ({
  availableTranslations,
  initialTranslations,
  form,
}: {
  availableTranslations?: NoticeTranslation[];
  initialTranslations: NoticeTranslationCreate[];
  form: FormInstance<PrivacyNoticeCreation>;
}) => {
  // Read translations reactively from the form store. The parent registers
  // `translations` via a hidden Form.Item so useWatch tracks changes even
  // when they're applied via setFieldValue (no direct Form.Item for the array).
  const translations =
    (Form.useWatch("translations", form) as
      | NoticeTranslationCreate[]
      | undefined) ?? [];

  const [activeLanguage, setActiveLanguage] = useState<string>(
    initialTranslations[0]?.language ?? "",
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
      translations.every((translation) => translation.language !== lang.id),
    )
    .map((lang) => ({ label: lang.name, value: lang.id as SupportedLanguage }));

  const isActiveTabOOB = !!availableTranslations?.some(
    (t) => t.language === activeLanguage,
  );

  const handleTabSelected = (language: string) => {
    setActiveLanguage(language);
  };

  const handleCreateLanguage = (language: SupportedLanguage) => {
    const availableTranslation = availableTranslations?.find(
      (translation) => translation.language === language,
    );
    const newTranslation: NoticeTranslationCreate = availableTranslation
      ? {
          ...availableTranslation,
          title: availableTranslation.title ?? "",
        }
      : {
          language,
          title: "",
          description: "",
        };
    setActiveLanguage(language);
    form.setFieldValue("translations", [...translations, newTranslation]);
  };

  const handleLanguageDeleted = (language: string) => {
    const updated = translations.filter((lang) => lang.language !== language);
    const newActiveLanguage =
      activeLanguage === language
        ? (updated[updated.length - 1]?.language ?? "")
        : activeLanguage;
    form.setFieldValue("translations", updated);
    setActiveLanguage(newActiveLanguage);
  };

  const getLanguageDisplayName = (lang: SupportedLanguage) =>
    allLanguages.find((language) => language.id === lang)?.name ?? lang;

  if (!translationsEnabled) {
    return (
      <Card title="Notice text">
        <NoticeFormFields index={0} />
      </Card>
    );
  }

  return (
    <Card title="Localizations">
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
        items={translations.map((translation) => ({
          key: translation.language,
          label: getLanguageDisplayName(translation.language),
          children: (
            <TranslationFormBlock
              index={translations.findIndex(
                (t) => t.language === translation.language,
              )}
              name={getLanguageDisplayName(translation.language)}
              isOOB={isActiveTabOOB}
            />
          ),
          closable: translations.length > 1,
        }))}
      />
    </Card>
  );
};

export { PrivacyNoticeTranslationForm };
