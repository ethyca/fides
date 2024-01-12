import {
  Box,
  Button,
  Flex,
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

  const languageOptions = ["English", "French", "Spanish"]
    .filter(
      (lang) =>
        !values.translations.some(
          (translation) => translation.language === lang
        )
    )
    .map((lang) => ({
      label: lang,
      value: lang,
    }));

  const handleSelectLanguage = (language: string) => {
    const newTranslation: NoticeTranslation = {
      language,
      title: "",
      description: "",
    };
    setFieldValue("translations", [...values.translations, newTranslation]);
    setIsSelectingLanguage(false);
  };

  return (
    <FormSection title="Translations">
      <Flex direction="row" grow={1}>
        <Tabs id="test" orientation="vertical" variant="soft-rounded">
          <HStack spacing={8} align="start">
            <VStack spacing={4}>
              <TabList>
                <VStack spacing={2}>
                  {values.translations.length ? (
                    values.translations.map((translation) => (
                      <Tab as={Button} w="100%" key={translation.language}>
                        {translation.language === "English"
                          ? "English (default language)"
                          : translation.language}
                      </Tab>
                    ))
                  ) : (
                    <Tab as={Button}>English (default language)</Tab>
                  )}
                </VStack>
              </TabList>
              {isSelectingLanguage ? (
                <CustomSelect
                  // TODO: using the custom select here causes it to set the "newLanguage" field on the form values, which we don't want
                  name="newLanguage"
                  options={languageOptions}
                  onChange={(e: ChangeEvent) => {
                    // @ts-ignore
                    handleSelectLanguage(e.value);
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
          </HStack>
        </Tabs>
      </Flex>
    </FormSection>
  );
};

export default PrivacyNoticeTranslationForm;
