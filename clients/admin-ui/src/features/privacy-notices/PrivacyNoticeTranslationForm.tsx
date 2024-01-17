import {
  Box,
  Button,
  HStack,
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

import FormSection from "~/features/common/form/FormSection";
import {
  CustomSelect,
  CustomTextArea,
  CustomTextInput,
} from "~/features/common/form/inputs";
import {
  getLanguageNameByTag,
  getLanguageOptionByTag,
  NewPrivacyNotice,
  NoticeTranslation,
} from "~/features/privacy-notices/form";

const TranslationFormBlock = ({ index }: { index: number }) => (
  <VStack width="100%" spacing={6}>
    <Text fontSize="sm">
      Configure your privacy notice, including consent mechanism, associated
      data uses, and the locations in which this should be displayed to users.
    </Text>
    <CustomTextInput
      autoFocus={index != 0}
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

const PrivacyNoticeTranslationForm = () => {
  const { values, setFieldValue } = useFormikContext<NewPrivacyNotice>();

  const [isSelectingLanguage, setIsSelectingLanguage] =
    useState<boolean>(false);
  const [tabIndex, setTabIndex] = useState<number>(0);

  const languageOptions = [
    "fr",
    "es",
    "pt",
    "de",
    "zh-Hans",
    "zh-Hant",
    "ja",
    "ru",
    "en-US",
    "en-GB",
  ]
    .filter(
      (lang) =>
        !values.translations.some(
          (translation) => translation.language === lang
        )
    )
    .map((lang) => getLanguageOptionByTag(lang))
    .sort((a, b) => a.label.localeCompare(b.label));

  const handleLanguageSelected = (language: string) => {
    const newTranslation: NoticeTranslation = {
      language,
      title: "",
      description: "",
    };
    setTabIndex(values.translations.length);
    setFieldValue("translations", [...values.translations, newTranslation]);
    setIsSelectingLanguage(false);
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
          minW="20%"
        >
          <TabList w="100%">
            <VStack spacing={2} w="100%">
              {values.translations.length ? (
                values.translations.map((translation) => (
                  <Tab
                    as={Button}
                    size="sm"
                    fontWeight="normal"
                    w="100%"
                    key={translation.language}
                    _selected={{ color: "white", bg: "gray.500" }}
                  >
                    {getLanguageNameByTag(translation.language)}
                  </Tab>
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
              <TabPanels w="100%">
                {values.translations.map((translation, idx) => (
                  <TabPanel key={translation.language}>
                    <TranslationFormBlock index={idx} />
                  </TabPanel>
                ))}
              </TabPanels>
            )}
          />
        </Box>
      </Tabs>
    </FormSection>
  );
};

export default PrivacyNoticeTranslationForm;
