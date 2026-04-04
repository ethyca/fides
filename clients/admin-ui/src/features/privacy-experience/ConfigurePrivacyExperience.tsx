import {
  Button,
  Drawer,
  Flex,
  Form,
  Icons,
  Segmented,
  Splitter,
  Switch,
  Tooltip,
  Typography,
  useMessage,
  useModal,
} from "fidesui";
import { omit } from "lodash";
import { useRouter } from "next/router";
import React, { useCallback, useRef, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { getErrorMessage } from "~/features/common/helpers";
import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/routes";
import { useGetConfigurationSettingsQuery } from "~/features/config-settings/config-settings.slice";
import {
  findLanguageDisplayName,
  TranslationWithLanguageName,
} from "~/features/privacy-experience/form/helpers";
import { useExperienceForm } from "~/features/privacy-experience/form/useExperienceForm";
import {
  selectAllLanguages,
  selectPage as selectLanguagePage,
  selectPageSize as selectLanguagePageSize,
  useGetAllLanguagesQuery,
} from "~/features/privacy-experience/language.slice";
import Preview from "~/features/privacy-experience/preview/Preview";
import {
  usePatchExperienceConfigMutation,
  usePostExperienceConfigMutation,
} from "~/features/privacy-experience/privacy-experience.slice";
import {
  PrivacyExperienceForm,
  TCF_PLACEHOLDER_ID,
} from "~/features/privacy-experience/PrivacyExperienceForm";
import PrivacyExperienceTranslationForm, {
  TranslationFormHandle,
} from "~/features/privacy-experience/PrivacyExperienceTranslationForm";
import { selectAllPrivacyNotices } from "~/features/privacy-notices/privacy-notices.slice";
import {
  ExperienceConfigCreate,
  ExperienceConfigResponse,
  ExperienceTranslation,
  SupportedLanguage,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

const ConfigurePrivacyExperience = ({
  passedInExperience,
  passedInTranslations,
}: {
  passedInExperience?: ExperienceConfigResponse;
  passedInTranslations?: ExperienceTranslation[];
}) => {
  const [postExperienceConfigMutation] = usePostExperienceConfigMutation();
  const [patchExperienceConfigMutation] = usePatchExperienceConfigMutation();

  const message = useMessage();

  const [isMobilePreview, setIsMobilePreview] = useState(false);
  const [mockGpcEnabled, setMockGpcEnabled] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const isBrowserGpcEnabled = window.navigator?.globalPrivacyControl === true;

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

  const { form, initialValues } = useExperienceForm(passedInExperience);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      // Use getFieldsValue(true) to include ALL fields, even those without
      // a visible Form.Item (e.g. fields managed by ScrollableList or
      // conditionally rendered switches).
      const cleanedValues = {
        ...form.getFieldsValue(true),
      } as ExperienceConfigCreate;
      // Ignore placeholder TCF notice. It is used only as a UX cue that TCF purposes will always exist
      cleanedValues.privacy_notice_ids =
        cleanedValues.privacy_notice_ids?.filter(
          (item) => item !== TCF_PLACEHOLDER_ID,
        );
      if (
        initialValues.tcf_configuration_id &&
        !cleanedValues.tcf_configuration_id
      ) {
        // If the TCF configuration gets cleared, set the TCF configuration ID to null to remove it on the DB side
        cleanedValues.tcf_configuration_id = null;
      }
      const valuesToSubmit = {
        ...cleanedValues,
        disabled: passedInExperience?.disabled ?? true,
        allow_language_selection:
          cleanedValues.translations && cleanedValues.translations.length > 1,
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
        message.error(getErrorMessage(result.error));
      } else {
        message.success(
          `Privacy experience successfully ${
            passedInExperience ? "updated" : "created"
          }`,
        );
        // Defer navigation to the next microtask so the message re-render
        // completes before the page transition starts unmounting components.
        // Without this, Ant v6 can throw a locale error when the message
        // state update overlaps with component unmounting.
        queueMicrotask(() => router.push(PRIVACY_EXPERIENCE_ROUTE));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const [translationToEdit, setTranslationToEdit] = useState<
    TranslationWithLanguageName | undefined
  >(undefined);

  const [usingOOBValues, setUsingOOBValues] = useState<boolean>(false);
  const [editingTranslationValues, setEditingTranslationValues] = useState<
    ExperienceTranslation | undefined
  >(undefined);

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

  const translationFormRef = useRef<TranslationFormHandle>(null);
  const modal = useModal();

  const closeTranslationDrawer = useCallback(() => {
    setTranslationToEdit(undefined);
    setUsingOOBValues(false);
    setEditingTranslationValues(undefined);
  }, []);

  /** Called by Cancel button or drawer close. Checks the local form for
   *  unsaved edits via the imperative handle and shows a confirmation modal
   *  if dirty. On discard, removes new (uncommitted) translations. */
  const handleLeaveTranslationForm = useCallback(() => {
    const isDirty = translationFormRef.current?.isDirty() ?? false;

    if (!isDirty) {
      // For new translations that were never saved, remove the placeholder.
      if (translationToEdit) {
        const initial = omit(
          translationToEdit,
          "name",
        ) as ExperienceTranslation;
        const isEditing = !!initial.title && !usingOOBValues;
        if (!isEditing) {
          const allTranslations = (form.getFieldValue("translations") ??
            []) as ExperienceTranslation[];
          const idx = allTranslations.findIndex(
            (t) => t.language === translationToEdit.language,
          );
          if (idx >= 0) {
            const updated = allTranslations.slice();
            updated.splice(idx, 1);
            form.setFieldValue("translations", updated);
          }
        }
      }
      closeTranslationDrawer();
      return;
    }

    if (!translationToEdit) {
      closeTranslationDrawer();
      return;
    }

    const initialTranslation = omit(
      translationToEdit,
      "name",
    ) as ExperienceTranslation;
    const isEditing = !!initialTranslation.title && !usingOOBValues;

    let unsavedMessage;
    if (!translationsEnabled) {
      unsavedMessage =
        "You have unsaved changes to this experience text. Discard changes?";
    } else if (isEditing) {
      unsavedMessage =
        "You have unsaved changes to this translation. Discard changes?";
    } else {
      unsavedMessage =
        "This translation has not been added to your experience.  Discard translation?";
    }

    modal.confirm({
      title: translationsEnabled ? "Translation not saved" : "Text not saved",
      content: <Typography.Text>{unsavedMessage}</Typography.Text>,
      okText: "Discard",
      cancelText: "Cancel",
      centered: true,
      icon: null,
      onOk: () => {
        // The local form never committed, so parent form has original values.
        // For new translations, remove the placeholder entry.
        if (!isEditing) {
          const allTranslations = (form.getFieldValue("translations") ??
            []) as ExperienceTranslation[];
          const idx = allTranslations.findIndex(
            (t) => t.language === translationToEdit.language,
          );
          if (idx >= 0) {
            const updated = allTranslations.slice();
            updated.splice(idx, 1);
            form.setFieldValue("translations", updated);
          }
        }
        closeTranslationDrawer();
      },
    });
  }, [
    translationToEdit,
    usingOOBValues,
    translationsEnabled,
    form,
    modal,
    closeTranslationDrawer,
  ]);

  return (
    <Form
      form={form}
      initialValues={initialValues}
      onFinish={handleSubmit}
      key={passedInExperience?.id ?? "create"}
      style={{ height: "100vh" }}
      component="form"
      layout="vertical"
    >
      <Flex className="size-full" data-testid="privacy-experience-detail-page">
        <Splitter>
          <Splitter.Panel min={300} defaultSize={300} max="50%" collapsible>
            <PrivacyExperienceForm
              form={form}
              allPrivacyNotices={allPrivacyNotices}
              translationsEnabled={translationsEnabled}
              initialValues={initialValues}
              onSelectTranslation={handleTranslationSelected}
              onCreateTranslation={handleCreateNewTranslation}
              isSubmitting={isSubmitting}
            />
          </Splitter.Panel>
          <Splitter.Panel>
            <Flex
              vertical
              className="size-full overflow-y-hidden"
              style={{ backgroundColor: "var(--ant-color-bg-layout)" }}
            >
              <Flex
                className="flex-row items-center p-4"
                style={{
                  backgroundColor: "var(--ant-color-bg-elevated)",
                  borderBottom: `1px solid var(--ant-color-border)`,
                }}
              >
                <Typography.Text strong>PREVIEW</Typography.Text>
                <div className="flex-1" />
                <Flex className="flex-row items-center gap-2">
                  <Tooltip
                    title={
                      isBrowserGpcEnabled
                        ? "GPC is enabled at the browser level. Disable it to use this toggle."
                        : undefined
                    }
                  >
                    <Switch
                      aria-label="Toggle GPC preview mode"
                      checkedChildren="GPC"
                      unCheckedChildren="GPC"
                      checked={
                        !isBrowserGpcEnabled
                          ? mockGpcEnabled
                          : isBrowserGpcEnabled
                      }
                      onChange={(value) => {
                        setMockGpcEnabled(value);
                        router.replace({
                          pathname: router.pathname,
                          query: {
                            ...router.query,
                            globalPrivacyControl: value.toString(),
                          },
                        });
                      }}
                      data-testid="gpc-preview-toggle"
                      disabled={isBrowserGpcEnabled}
                    />
                  </Tooltip>
                  <Segmented
                    options={[
                      {
                        value: "mobile",
                        icon: <Icons.Mobile title="Mobile" />,
                      },
                      {
                        value: "desktop",
                        icon: <Icons.Screen title="Desktop" />,
                      },
                    ]}
                    defaultValue="desktop"
                    onChange={(value) => setIsMobilePreview(value === "mobile")}
                  />
                </Flex>
              </Flex>
              <Preview
                allPrivacyNotices={allPrivacyNotices}
                initialValues={initialValues}
                translation={translationToEdit}
                editingTranslationValues={editingTranslationValues}
                isMobilePreview={isMobilePreview}
                mockGpcEnabled={mockGpcEnabled}
              />
            </Flex>
          </Splitter.Panel>
        </Splitter>
      </Flex>
      <Drawer
        title={
          translationsEnabled
            ? `Edit ${translationToEdit?.name} translation`
            : "Edit experience text"
        }
        open={!!translationToEdit}
        onClose={handleLeaveTranslationForm}
        placement="left"
        mask={false}
        footer={
          translationToEdit && (
            <Flex justify="flex-end" gap="small">
              <Button
                onClick={handleLeaveTranslationForm}
                data-testid="translation-cancel-btn"
              >
                Cancel
              </Button>
              <Button
                onClick={() => translationFormRef.current?.save()}
                type="primary"
                data-testid="translation-save-btn"
              >
                {!!translationToEdit?.title && !usingOOBValues
                  ? "Done"
                  : "Add translation"}
              </Button>
            </Flex>
          )
        }
      >
        {!!translationToEdit && (
          <PrivacyExperienceTranslationForm
            ref={translationFormRef}
            parentForm={form}
            translation={translationToEdit}
            translationsEnabled={translationsEnabled}
            isOOB={usingOOBValues}
            onClose={closeTranslationDrawer}
            onValuesChange={setEditingTranslationValues}
          />
        )}
      </Drawer>
    </Form>
  );
};

export default ConfigurePrivacyExperience;
