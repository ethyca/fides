import {
  AntButton as Button,
  AntFlex as Flex,
  AntRadio as Radio,
  Spacer,
  Text,
  useToast,
  theme,
} from "fidesui";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import React, { useState } from "react";
import * as Yup from "yup";

import { useAppSelector } from "~/app/hooks";
import { getErrorMessage } from "~/features/common/helpers";
import { DesktopIcon } from "~/features/common/Icon/DesktopIcon";
import { MobileIcon } from "~/features/common/Icon/MobileIcon";
import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useGetConfigurationSettingsQuery } from "~/features/config-settings/config-settings.slice";
import {
  defaultInitialValues,
  findLanguageDisplayName,
  getTranslationFormFields,
  transformConfigResponseToCreate,
  TranslationWithLanguageName,
} from "~/features/privacy-experience/form/helpers";
import { FIELD_VALIDATION_DATA } from "~/features/privacy-experience/form/translations-form-validations";
import {
  selectAllLanguages,
  selectPage as selectLanguagePage,
  selectPageSize as selectLanguagePageSize,
  useGetAllLanguagesQuery,
} from "~/features/privacy-experience/language.slice";
import Preview from "~/features/privacy-experience/Preview";
import {
  usePatchExperienceConfigMutation,
  usePostExperienceConfigMutation,
} from "~/features/privacy-experience/privacy-experience.slice";
import { PrivacyExperienceForm } from "~/features/privacy-experience/PrivacyExperienceForm";
import PrivacyExperienceTranslationForm from "~/features/privacy-experience/PrivacyExperienceTranslationForm";
import { selectAllPrivacyNotices } from "~/features/privacy-notices/privacy-notices.slice";
import {
  ComponentType,
  ExperienceConfigCreate,
  ExperienceConfigResponse,
  ExperienceTranslation,
  ExperienceTranslationCreate,
  SupportedLanguage,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

const buildTranslationSchema = (componentType: ComponentType): Yup.Schema => {
  const formFields = getTranslationFormFields(componentType);
  const schema: Partial<Record<keyof ExperienceTranslationCreate, Yup.Schema>> =
    {};

  Object.entries(formFields).forEach(([field, config]) => {
    const fieldKey = field as keyof ExperienceTranslationCreate;
    if (config.included) {
      const fieldData = FIELD_VALIDATION_DATA[fieldKey];
      schema[fieldKey] = config.required
        ? fieldData.validation.required().label(fieldData.label)
        : fieldData.validation.nullable().label(fieldData.label);
    }
  });

  return Yup.object().shape(schema);
};

const translationSchema = ({
  componentType,
}: {
  componentType: ComponentType;
}) => buildTranslationSchema(componentType);

const validationSchema = Yup.object().shape({
  name: Yup.string().required().label("Experience name"),
  component: Yup.string().required().label("Experience type"),
  translations: Yup.array().when("component", ([component], schema) =>
    schema.of(translationSchema({ componentType: component })),
  ),
});

const ConfigurePrivacyExperience = ({
  passedInExperience,
  passedInTranslations,
}: {
  passedInExperience?: ExperienceConfigResponse;
  passedInTranslations?: ExperienceTranslation[];
}) => {
  const [postExperienceConfigMutation] = usePostExperienceConfigMutation();
  const [patchExperienceConfigMutation] = usePatchExperienceConfigMutation();

  const toast = useToast();

  const [isMobilePreview, setIsMobilePreview] = useState(false);

  const router = useRouter();

  const { data: appConfig } = useGetConfigurationSettingsQuery({
    api_set: false,
  });
  const translationsEnabled =
    appConfig?.plus_consent_settings?.enable_translations;

  const languagePage = useAppSelector(selectLanguagePage);
  const languagePageSize = useAppSelector(selectLanguagePageSize);
  useGetAllLanguagesQuery({ page: languagePage, size: languagePageSize });
  const allLanguages = useAppSelector(selectAllLanguages);
  const allPrivacyNotices = useAppSelector(selectAllPrivacyNotices);

  const initialValues = passedInExperience
    ? {
        ...defaultInitialValues,
        ...transformConfigResponseToCreate(passedInExperience),
      }
    : defaultInitialValues;

  const handleSubmit = async (values: ExperienceConfigCreate) => {
    // Ignore placeholder TCF notice. It is used only as a UX cue that TCF purposes will always exist
    // eslint-disable-next-line no-param-reassign
    values.privacy_notice_ids = values.privacy_notice_ids?.filter(
      (item) => item !== "tcf_purposes_placeholder",
    );
    const valuesToSubmit = {
      ...values,
      disabled: passedInExperience?.disabled ?? true,
      allow_language_selection:
        values.translations && values.translations.length > 1,
    };

    let result;
    if (!passedInExperience) {
      result = await postExperienceConfigMutation(valuesToSubmit);
    } else {
      const { component, ...payload } = valuesToSubmit;
      result = await patchExperienceConfigMutation({
        ...payload,
        id: passedInExperience.id,
      });
    }

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          `Privacy experience successfully ${
            passedInExperience ? "updated" : "created"
          }`,
        ),
      );
      router.push(PRIVACY_EXPERIENCE_ROUTE);
    }
  };

  const [translationToEdit, setTranslationToEdit] = useState<
    TranslationWithLanguageName | undefined
  >(undefined);

  const [usingOOBValues, setUsingOOBValues] = useState<boolean>(false);

  const handleTranslationSelected = (translation: ExperienceTranslation) => {
    setTranslationToEdit({
      ...translation,
      name: findLanguageDisplayName(translation, allLanguages),
    });
  };

  const handleCreateNewTranslation = (language: SupportedLanguage) => {
    const availableTranslation = passedInTranslations?.find(
      (t) => t.language === language,
    );
    if (availableTranslation) {
      setUsingOOBValues(true);
    }
    return (
      availableTranslation ?? {
        language,
        is_default: false,
      }
    );
  };

  const handleExitTranslationForm = () => {
    setTranslationToEdit(undefined);
    setUsingOOBValues(false);
  };

  return (
    <Formik
      initialValues={initialValues as ExperienceConfigCreate}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={validationSchema}
    >
      <Form style={{ height: "100vh" }}>
        <Flex
          className="w-full h-full"
          data-testid="privacy-experience-detail-page"
        >
          {translationToEdit ? (
            <PrivacyExperienceTranslationForm
              translation={translationToEdit}
              translationsEnabled={translationsEnabled}
              isOOB={usingOOBValues}
              onReturnToMainForm={handleExitTranslationForm}
            />
          ) : (
            <PrivacyExperienceForm
              allPrivacyNotices={allPrivacyNotices}
              translationsEnabled={translationsEnabled}
              onSelectTranslation={handleTranslationSelected}
              onCreateTranslation={handleCreateNewTranslation}
            />
          )}
          <Flex
            vertical
            className="w-full overflow-y-hidden"
            style={{ backgroundColor: theme.colors.gray[50] }}
          >
            <Flex
              className="flex-row p-4 items-center"
              style={{
                backgroundColor: theme.colors.white,
                borderBottom: `1px solid ${theme.colors.gray[100]}`,
              }}
            >
              <Text fontSize="md" fontWeight="semibold">
                PREVIEW
              </Text>
              <Spacer />
              <Radio.Group
                onChange={(e) => setIsMobilePreview(e.target.value)}
                defaultValue={false}
              >
                <Radio.Button value={true} title="View mobile preview">
                  <MobileIcon />
                </Radio.Button>
                <Radio.Button value={false} title="View desktop preview">
                  <DesktopIcon />
                </Radio.Button>
              </Radio.Group>
            </Flex>
            <Preview
              allPrivacyNotices={allPrivacyNotices}
              initialValues={initialValues}
              translation={translationToEdit}
              isMobilePreview={isMobilePreview}
            />
          </Flex>
        </Flex>
      </Form>
    </Formik>
  );
};

export default ConfigurePrivacyExperience;
