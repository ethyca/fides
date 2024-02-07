import { Button, DeleteIcon, Flex, IconButton, Text } from "@fidesui/react";
import { useFormikContext } from "formik";
import localeCodes, { ILocale } from "locale-codes";
import { ChangeEvent, useState } from "react";
import { CustomSelect } from "~/features/common/form/inputs";
import {
  PrivacyExperienceTranslation,
  NewPrivacyExperience,
} from "~/features/privacy-experience/NewPrivacyExperienceForm";

const TranslationTabButton = ({
  translation,
  onDelete,
}: {
  translation: PrivacyExperienceTranslation;
  onDelete?: (language: string) => void;
}) => {
  return (
    <Flex gap={2} direction="row" w="full">
      <Button
        variant="outline"
        w="full"
        size="sm"
        fontWeight="normal"
        key={translation.language}
        _selected={{ color: "white", bg: "gray.500" }}
      >
        {localeCodes.getByTag(translation.language).name}
      </Button>
      {onDelete ? (
        <IconButton
          aria-label={"delete-translation"}
          variant="outline"
          size="sm"
          onClick={() => onDelete(translation.language)}
        >
          <DeleteIcon boxSize={4} />
        </IconButton>
      ) : null}
    </Flex>
  );
};

const PrivacyExperienceLanguageMenu = ({
  translations,
}: {
  translations: PrivacyExperienceTranslation[];
}) => {
  const [isSelectingLanguage, setIsSelectingLanguage] =
    useState<boolean>(false);

  const { values, setFieldValue } = useFormikContext<NewPrivacyExperience>();

  // TEMP
  const getLanguageOption = (locale: ILocale) => {
    return {
      label: locale.location
        ? `${locale.name} (${locale.location})`
        : locale.name,
      value: locale.tag,
    };
  };

  const languageOptions = localeCodes.all
    .filter((locale) =>
      translations.every((translation) => translation.language !== locale.tag)
    )
    .map((locale) => getLanguageOption(locale))
    .sort((a, b) => a.label.localeCompare(b.label));

  const handleAddLanguage = (language: string) => {
    const newTranslation: PrivacyExperienceTranslation = {
      language,
      is_default: false,
    };
    setFieldValue("translations", [...values.translations, newTranslation]);
    setIsSelectingLanguage(false);
  };

  const handleLanguageDeleted = (tag: string) => {
    const newTranslations = values.translations
      .slice()
      .filter((lang) => lang.language !== tag);
    setFieldValue("translations", newTranslations);
  };

  return (
    <>
      {translations.map((t) => (
        <TranslationTabButton
          translation={t}
          onDelete={!t.is_default ? handleLanguageDeleted : undefined}
        />
      ))}
      {isSelectingLanguage ? (
        <CustomSelect
          name="newLanguage"
          options={languageOptions}
          placeholder="Select a language..."
          isSearchable
          autoFocus
          onChange={(e: ChangeEvent<HTMLSelectElement>) =>
            // @ts-ignore
            handleAddLanguage(e.value)
          }
        />
      ) : (
        <Button onClick={() => setIsSelectingLanguage(true)}>
          Add a language
        </Button>
      )}
    </>
  );
};

export default PrivacyExperienceLanguageMenu;
