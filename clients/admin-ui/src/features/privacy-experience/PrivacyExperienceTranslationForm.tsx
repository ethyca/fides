import {
  Alert,
  Button,
  Flex,
  Form,
  Input,
  Switch,
  Typography,
  useModal,
} from "fidesui";
import { isEqual } from "lodash";
import { useEffect, useMemo, useState } from "react";

import InfoBox from "~/features/common/InfoBox";
import { BackButtonNonLink } from "~/features/common/nav/BackButton";
import {
  getTranslationFormFields,
  TranslationWithLanguageName,
} from "~/features/privacy-experience/form/helpers";
import { ExperienceFormInstance } from "~/features/privacy-experience/form/useExperienceForm";
import { ComponentType, ExperienceTranslation } from "~/types/api";

import { ConfigColumnLayout } from "./ConfigColumnLayout";

export const OOBTranslationNotice = ({
  languageName,
}: {
  languageName: string;
}) => (
  <Alert
    showIcon
    description={`This is a default translation provided by Fides. If you've modified the default English language text, these translations will not match, so verify any changes with a native ${languageName} speaker before using.`}
    data-testid="oob-translation-notice"
  />
);

const PrivacyExperienceTranslationForm = ({
  form,
  translation,
  translationsEnabled,
  isOOB,
  onReturnToMainForm,
}: {
  form: ExperienceFormInstance;
  translation: TranslationWithLanguageName;
  translationsEnabled?: boolean;
  isOOB?: boolean;
  onReturnToMainForm: () => void;
}) => {
  const component = Form.useWatch("component", form);

  // store the initial translation so we can undo changes on discard
  const initialTranslation = useMemo(() => {
    const { name, ...rest } = translation;
    return rest as ExperienceTranslation;
  }, [translation]);
  const isEditing = !!initialTranslation.title && !isOOB;

  const formConfig = getTranslationFormFields(component);

  // "translations" is not registered as a single Form.Item (it would conflict with
  // nested name paths like ['translations', 0, 'title']). Read directly from the store.
  const allTranslations = form.getFieldValue("translations") as
    | ExperienceTranslation[]
    | undefined;

  const translationIndex =
    allTranslations?.findIndex(
      (t: ExperienceTranslation) => t.language === translation.language,
    ) ?? -1;

  // Watch the specific nested translation to get reactive updates when its fields change.
  const currentTranslation = Form.useWatch(
    ["translations", translationIndex],
    form,
  ) as ExperienceTranslation | undefined;

  const translationIsTouched = !isEqual(currentTranslation, initialTranslation);

  // Re-check translation validation errors reactively when values change.
  // currentTranslation is derived from Form.useWatch so it updates on every edit.
  // setTimeout(0) defers the check until after Ant's synchronous validation cycle.
  const [hasTranslationErrors, setHasTranslationErrors] = useState(false);
  useEffect(() => {
    if (translationIndex < 0) {
      setHasTranslationErrors(false);
      return undefined;
    }
    const timer = setTimeout(() => {
      const fieldErrors = form.getFieldsError();
      const hasErrors = fieldErrors.some(
        ({ name, errors }) =>
          Array.isArray(name) &&
          name[0] === "translations" &&
          name[1] === translationIndex &&
          errors.length > 0,
      );
      setHasTranslationErrors(hasErrors);
    }, 0);
    return () => clearTimeout(timer);
  }, [form, translationIndex, currentTranslation]);

  const modal = useModal();

  let unsavedChangesMessage;
  if (!translationsEnabled) {
    unsavedChangesMessage =
      "You have unsaved changes to this experience text. Discard changes?";
  } else {
    unsavedChangesMessage = isEditing
      ? "You have unsaved changes to this translation. Discard changes?"
      : "This translation has not been added to your experience.  Discard translation?";
  }

  const discardChanges = () => {
    const newTranslations = (allTranslations ?? []).slice();
    // when editing, revert all changes to the translation being edited
    if (isEditing) {
      newTranslations[translationIndex] = {
        ...initialTranslation,
        title: initialTranslation.title!,
        description: initialTranslation.description!,
      };
    }
    // when creating, just get rid of it
    else {
      newTranslations.splice(translationIndex, 1);
    }
    form.setFieldValue("translations", newTranslations);
    onReturnToMainForm();
  };

  const handleLeaveForm = () => {
    if (translationIsTouched || isOOB) {
      modal.confirm({
        title: translationsEnabled ? "Translation not saved" : "Text not saved",
        content: <Typography.Text>{unsavedChangesMessage}</Typography.Text>,
        okText: "Discard",
        cancelText: "Cancel",
        centered: true,
        icon: null,
        onOk: discardChanges,
      });
    } else {
      onReturnToMainForm();
    }
  };

  const setNewDefaultTranslation = (newDefaultIndex: number) => {
    const newTranslations = (allTranslations ?? []).map(
      (t: ExperienceTranslation, idx: number) => ({
        ...t,
        is_default: idx === newDefaultIndex,
      }),
    );
    // move the new default to first in the array
    newTranslations.unshift(newTranslations.splice(newDefaultIndex, 1)[0]);
    form.setFieldValue("translations", newTranslations);
    onReturnToMainForm();
  };

  const handleSaveTranslation = () => {
    if (currentTranslation?.is_default && !initialTranslation.is_default) {
      modal.confirm({
        title: "Update default language",
        content: (
          <Typography.Text>
            Are you sure you want to update the default language of this
            experience?
          </Typography.Text>
        ),
        okText: "Continue",
        cancelText: "Cancel",
        centered: true,
        icon: null,
        onOk: () => setNewDefaultTranslation(translationIndex),
      });
    } else {
      onReturnToMainForm();
    }
  };

  const buttonPanel = (
    <Flex
      justify="space-between"
      className="sticky bottom-0 z-10 bg-white p-4"
      style={{ borderTop: "1px solid var(--ant-color-border)" }}
    >
      <Button onClick={handleLeaveForm} data-testid="cancel-btn">
        Cancel
      </Button>
      <Button
        onClick={handleSaveTranslation}
        type="primary"
        data-testid="save-btn"
        disabled={(!translationIsTouched && !isOOB) || hasTranslationErrors}
      >
        {isEditing ? "Save" : "Add translation"}
      </Button>
    </Flex>
  );

  if (translationIndex < 0) {
    return null;
  }

  const fieldPrefix = ["translations", translationIndex];

  return (
    <ConfigColumnLayout buttonPanel={buttonPanel}>
      <BackButtonNonLink onClick={handleLeaveForm} mt={4} />
      <Typography.Title level={5} style={{ margin: 0 }}>
        {translationsEnabled
          ? `Edit ${translation.name} translation`
          : "Edit experience text"}
      </Typography.Title>
      {isOOB ? <OOBTranslationNotice languageName={translation.name} /> : null}
      {translationsEnabled && (
        <Flex justify="space-between" align="center">
          <Typography.Text className="text-xs">
            Default language
          </Typography.Text>
          <Form.Item
            name={[...fieldPrefix, "is_default"]}
            valuePropName="checked"
            noStyle
          >
            <Switch
              disabled={Boolean(initialTranslation.is_default)}
              size="small"
              data-testid={`input-translations.${translationIndex}.is_default`}
            />
          </Form.Item>
        </Flex>
      )}

      <Form.Item
        name={[...fieldPrefix, "title"]}
        label="Title"
        rules={[{ required: true, message: "Title is required" }]}
      >
        <Input
          required
          data-testid={`input-translations.${translationIndex}.title`}
        />
      </Form.Item>
      <Form.Item
        name={[...fieldPrefix, "description"]}
        label="Description"
        rules={[{ required: true, message: "Description is required" }]}
      >
        <Input.TextArea
          required
          data-testid={`input-translations.${translationIndex}.description`}
        />
      </Form.Item>
      {(component === ComponentType.BANNER_AND_MODAL ||
        component === ComponentType.TCF_OVERLAY) && (
        <>
          <Form.Item
            name={[...fieldPrefix, "banner_title"]}
            label="Banner title (optional)"
            tooltip="A separate title for the banner (defaults to main title)"
          >
            <Input
              data-testid={`input-translations.${translationIndex}.banner_title`}
            />
          </Form.Item>
          <Form.Item
            name={[...fieldPrefix, "banner_description"]}
            label="Banner description (optional)"
            tooltip="A separate description for the banner (defaults to main description)"
          >
            <Input.TextArea
              data-testid={`input-translations.${translationIndex}.banner_description`}
            />
          </Form.Item>
        </>
      )}
      {component === ComponentType.TCF_OVERLAY && (
        <Form.Item
          name={[...fieldPrefix, "purpose_header"]}
          label="Purpose header (optional)"
          tooltip="Appears above the Purpose list section of the TCF banner"
        >
          <Input
            data-testid={`input-translations.${translationIndex}.purpose_header`}
          />
        </Form.Item>
      )}
      <Form.Item
        name={[...fieldPrefix, "accept_button_label"]}
        label={`"Accept" button label`}
        rules={[{ required: true, message: "Accept button label is required" }]}
      >
        <Input
          required
          data-testid={`input-translations.${translationIndex}.accept_button_label`}
        />
      </Form.Item>
      <Form.Item
        name={[...fieldPrefix, "reject_button_label"]}
        label={`"Reject" button label`}
        rules={[{ required: true, message: "Reject button label is required" }]}
      >
        <Input
          required
          data-testid={`input-translations.${translationIndex}.reject_button_label`}
        />
      </Form.Item>
      {formConfig.privacy_preferences_link_label?.included && (
        <Form.Item
          name={[...fieldPrefix, "privacy_preferences_link_label"]}
          label={`"Manage privacy preferences" button label`}
          rules={
            formConfig.privacy_preferences_link_label?.required
              ? [
                  {
                    required: true,
                    message: "Privacy preferences link label is required",
                  },
                ]
              : undefined
          }
        >
          <Input
            required={formConfig.privacy_preferences_link_label?.required}
            data-testid={`input-translations.${translationIndex}.privacy_preferences_link_label`}
          />
        </Form.Item>
      )}
      {formConfig.save_button_label?.included && (
        <Form.Item
          name={[...fieldPrefix, "save_button_label"]}
          label={`"Save" button label`}
          rules={
            formConfig.save_button_label.required
              ? [
                  {
                    required: true,
                    message: "Save button label is required",
                  },
                ]
              : undefined
          }
        >
          <Input
            required={formConfig.save_button_label?.required}
            data-testid={`input-translations.${translationIndex}.save_button_label`}
          />
        </Form.Item>
      )}
      {formConfig.acknowledge_button_label?.included && (
        <Form.Item
          name={[...fieldPrefix, "acknowledge_button_label"]}
          label={`"Acknowledge" button label`}
          rules={
            formConfig.acknowledge_button_label.required
              ? [
                  {
                    required: true,
                    message: "Acknowledge button label is required",
                  },
                ]
              : undefined
          }
        >
          <Input
            required={formConfig.acknowledge_button_label?.required}
            data-testid={`input-translations.${translationIndex}.acknowledge_button_label`}
          />
        </Form.Item>
      )}
      {formConfig.privacy_policy_link_label?.included && (
        <Form.Item
          name={[...fieldPrefix, "privacy_policy_link_label"]}
          label="Privacy policy link label (optional)"
        >
          <Input
            data-testid={`input-translations.${translationIndex}.privacy_policy_link_label`}
          />
        </Form.Item>
      )}
      {formConfig.privacy_policy_url?.included && (
        <Form.Item
          name={[...fieldPrefix, "privacy_policy_url"]}
          label="Privacy policy link URL (optional)"
          rules={[{ type: "url", message: "Must be a valid URL" }]}
        >
          <Input
            data-testid={`input-translations.${translationIndex}.privacy_policy_url`}
          />
        </Form.Item>
      )}
      {formConfig.modal_link_label?.included && (
        <Form.Item
          name={[...fieldPrefix, "modal_link_label"]}
          label="Trigger link label (optional)"
          tooltip="Include text here if you would like the Fides CMP to manage the copy of the button that is included on your site to open the CMP."
        >
          <Input
            data-testid={`input-translations.${translationIndex}.modal_link_label`}
          />
        </Form.Item>
      )}
      {formConfig.gpc_label?.included && (
        <Form.Item
          name={[...fieldPrefix, "gpc_label"]}
          label="GPC label (optional)"
          tooltip="The label shown next to the GPC badge (e.g. 'Global Privacy Control')"
        >
          <Input
            data-testid={`input-translations.${translationIndex}.gpc_label`}
          />
        </Form.Item>
      )}
      {formConfig.gpc_title?.included && (
        <Form.Item
          name={[...fieldPrefix, "gpc_title"]}
          label="GPC title (optional)"
          tooltip="Title shown in the GPC info section (e.g. 'Global Privacy Control detected')"
        >
          <Input
            data-testid={`input-translations.${translationIndex}.gpc_title`}
          />
        </Form.Item>
      )}
      {formConfig.gpc_description?.included && (
        <Form.Item
          name={[...fieldPrefix, "gpc_description"]}
          label="GPC description (optional)"
          tooltip="Description shown when GPC preference is honored"
        >
          <Input.TextArea
            data-testid={`input-translations.${translationIndex}.gpc_description`}
          />
        </Form.Item>
      )}
      {formConfig.gpc_status_applied_label?.included && (
        <Form.Item
          name={[...fieldPrefix, "gpc_status_applied_label"]}
          label="GPC 'Applied' status label (optional)"
          tooltip="Text shown when GPC is applied (e.g. 'Applied')"
        >
          <Input
            data-testid={`input-translations.${translationIndex}.gpc_status_applied_label`}
          />
        </Form.Item>
      )}
      {formConfig.gpc_status_overridden_label?.included && (
        <Form.Item
          name={[...fieldPrefix, "gpc_status_overridden_label"]}
          label="GPC 'Overridden' status label (optional)"
          tooltip="Text shown when GPC is overridden (e.g. 'Overridden')"
        >
          <Input
            data-testid={`input-translations.${translationIndex}.gpc_status_overridden_label`}
          />
        </Form.Item>
      )}
    </ConfigColumnLayout>
  );
};
export default PrivacyExperienceTranslationForm;
