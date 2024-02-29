import {
  Box,
  Button,
  DeleteIcon,
  Flex,
  HStack,
  IconButton,
  SmallAddIcon,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Text,
  VStack,
} from "@fidesui/react";
import { FieldArray, useFormikContext } from "formik";
import { ChangeEvent, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import FormSection from "~/features/common/form/FormSection";
import {
  CustomSelect,
  CustomTextArea,
  CustomTextInput,
} from "~/features/common/form/inputs";
import {
  selectAllLanguages,
  selectPage,
  selectPageSize,
  useGetAllLanguagesQuery,
} from "~/features/privacy-experience/language.slice";
import {
  NoticeTranslationCreate,
  PrivacyNoticeCreation,
  SupportedLanguage,
} from "~/types/api";

const TranslationFormBlock = ({ index }: { index: number }) => (
  <VStack width="100%" spacing={6}>
    <Text fontSize="sm">
      Configure your privacy notice, including consent mechanism, associated
      data uses, and the locations in which this should be displayed to users.
    </Text>
    <CustomTextInput
      autoFocus={index !== 0}
      name={`translations.${index}.title`}
      label="Title of consent notice as displayed to user"
      variant="stacked"
    />
    <CustomTextArea
      name={`translations.${index}.description`}
      label="Privacy notice displayed to the user"
      variant="stacked"
    />
  </VStack>
);

const TranslationTabButton = ({
  translation,
  onLanguageDeleted,
}: {
  translation: NoticeTranslationCreate;
  onLanguageDeleted?: (language: string) => void;
}) => (
  <Flex gap={2} direction="row" w="100%">
    <Tab
      as={Button}
      variant="outline"
      size="sm"
      fontWeight="normal"
      w="100%"
      key={translation.language}
      _selected={{ color: "white", bg: "gray.500" }}
    >
      {translation.language}
    </Tab>
    {onLanguageDeleted ? (
      <IconButton
        aria-label="Delete translation"
        variant="outline"
        size="sm"
        onClick={() => onLanguageDeleted(translation.language)}
      >
        <DeleteIcon boxSize={4} />
      </IconButton>
    ) : null}
  </Flex>
);

const PrivacyNoticeTranslationForm = () => {
  const { values, setFieldValue } = useFormikContext<PrivacyNoticeCreation>();

  const [isSelectingLanguage, setIsSelectingLanguage] =
    useState<boolean>(false);
  const [tabIndex, setTabIndex] = useState<number>(0);

  const languagePage = useAppSelector(selectPage);
  const languagePageSize = useAppSelector(selectPageSize);
  useGetAllLanguagesQuery({ page: languagePage, size: languagePageSize });
  const allLanguages = useAppSelector(selectAllLanguages);

  const languageOptions = allLanguages
    .filter((lang) =>
      values.translations?.every(
        (translation) => translation.language !== lang.id
      )
    )
    .map((lang) => ({ label: lang.name, value: lang.id }));

  const handleLanguageSelected = (language: string) => {
    const newTranslation: NoticeTranslationCreate = {
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

  return (
    <FormSection title="Localizations">
      <Tabs
        index={tabIndex}
        onChange={setTabIndex}
        as={HStack}
        spacing={8}
        align="start"
        grow={1}
        w="100%"
        orientation="vertical"
        variant="unstyled"
      >
        <VStack
          spacing={4}
          outline="1px solid"
          outlineColor="gray.200"
          p={4}
          borderRadius="md"
          minW="30%"
        >
          <TabList w="100%">
            <VStack spacing={2} w="100%">
              {values.translations?.length ? (
                values.translations.map((translation) => (
                  <TranslationTabButton
                    translation={translation}
                    key={translation.language}
                    onLanguageDeleted={handleLanguageDeleted}
                  />
                ))
              ) : (
                <Tab as={Button}>English</Tab>
              )}
            </VStack>
          </TabList>
          {isSelectingLanguage ? (
            <CustomSelect
              // TODO: using the CustomSelect here causes it to set the "newLanguage" field on the Formik form values, which we don't want
              name="newLanguage"
              options={languageOptions}
              placeholder="Select a language..."
              isSearchable
              autoFocus
              onChange={(e: ChangeEvent) => {
                // @ts-ignore
                handleLanguageSelected(e.value);
              }}
            />
          ) : null}
          {!isSelectingLanguage && languageOptions.length ? (
            <Button
              leftIcon={<SmallAddIcon boxSize={6} />}
              size="sm"
              onClick={() => setIsSelectingLanguage(true)}
            >
              Add a language
            </Button>
          ) : null}
        </VStack>
        <Box w="100%">
          <FieldArray
            name="translations"
            render={() => (
              <TabPanels w="100%">{values.translations[0].language}</TabPanels>
            )}
          />
        </Box>
      </Tabs>
    </FormSection>
  );
};

export default PrivacyNoticeTranslationForm;
