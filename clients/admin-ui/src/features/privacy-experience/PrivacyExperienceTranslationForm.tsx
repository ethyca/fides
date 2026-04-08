import { Alert, Form, Input, Typography, useModal } from "fidesui";
import React, { useImperativeHandle, useMemo } from "react";

import TemplateVariableInput, {
  TemplateVariable,
} from "~/features/common/TemplateVariableInput";
import {
  getTranslationFormFields,
  TranslationWithLanguageName,
} from "~/features/privacy-experience/form/helpers";
import { ExperienceFormInstance } from "~/features/privacy-experience/form/useExperienceForm";
import { ComponentType, ExperienceTranslation } from "~/types/api";

import { SwitchField } from "./form/SwitchField";

const GPC_VARIABLES: TemplateVariable[] = [
  {
    name: "GPC_START",
    description: "Start of text shown only when a GPC signal is detected",
  },
  {
    name: "GPC_END",
    description: "End of GPC-conditional block",
  },
  {
    name: "NO_GPC_START",
    description: "Start of text shown only when no GPC signal is detected",
  },
  {
    name: "NO_GPC_END",
    description: "End of no-GPC block",
  },
];

const DESCRIPTION_VARIABLES: TemplateVariable[] = [
  ...GPC_VARIABLES,
  {
    name: "VENDOR_COUNT_LINK",
    description:
      "A clickable link showing the number of vendors; tapping it opens the vendor list",
  },
];

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

export interface TranslationFormHandle {
  /** Validate, commit to parent form, and close. */
  save: () => void;
  /** Returns true when the local form has been edited or is an OOB import. */
  isDirty: () => boolean;
  /** Returns the current local form values for live preview. */
  getValues: () => ExperienceTranslation;
}

interface TranslationFormProps {
  parentForm: ExperienceFormInstance;
  translation: TranslationWithLanguageName;
  translationsEnabled?: boolean;
  isOOB?: boolean;
  onClose: () => void;
  /** Called on every local form value change, for live preview updates. */
  onValuesChange?: (values: ExperienceTranslation) => void;
}

const PrivacyExperienceTranslationForm = React.forwardRef<
  TranslationFormHandle,
  TranslationFormProps
>(
  (
    {
      parentForm,
      translation,
      translationsEnabled,
      isOOB,
      onClose,
      onValuesChange,
    },
    ref,
  ) => {
    const component = Form.useWatch("component", parentForm);

    const initialTranslation = useMemo(() => {
      const { name, ...rest } = translation;
      return rest as ExperienceTranslation;
    }, [translation]);

    const formConfig = getTranslationFormFields(component);

    const allTranslations = parentForm.getFieldValue("translations") as
      | ExperienceTranslation[]
      | undefined;

    const translationIndex =
      allTranslations?.findIndex(
        (t: ExperienceTranslation) => t.language === translation.language,
      ) ?? -1;

    // Own form instance so edits don't dirty the parent form until saved.
    const [localForm] = Form.useForm<ExperienceTranslation>();

    const modal = useModal();

    /** Write local form values into the parent form's translations array. */
    const commitToParentForm = () => {
      const localValues = localForm.getFieldsValue(
        true,
      ) as ExperienceTranslation;
      const currentTranslations =
        (parentForm.getFieldValue("translations") as
          | ExperienceTranslation[]
          | undefined) ?? [];
      const updated = currentTranslations.slice();
      updated[translationIndex] = {
        ...updated[translationIndex],
        ...localValues,
      };
      // Cast needed: ExperienceTranslation allows `null` on some fields but
      // antd's setFieldsValue types strip `null`. Runtime behavior is correct.
      parentForm.setFieldsValue({
        translations: updated,
      } as Parameters<typeof parentForm.setFieldsValue>[0]);
    };

    const setNewDefaultTranslation = (newDefaultIndex: number) => {
      commitToParentForm();
      const freshTranslations = parentForm.getFieldValue(
        "translations",
      ) as ExperienceTranslation[];
      const newTranslations = freshTranslations.map(
        (t: ExperienceTranslation, idx: number) => ({
          ...t,
          is_default: idx === newDefaultIndex,
        }),
      );
      newTranslations.unshift(newTranslations.splice(newDefaultIndex, 1)[0]);
      parentForm.setFieldsValue({
        translations: newTranslations,
      } as Parameters<typeof parentForm.setFieldsValue>[0]);
      onClose();
    };

    const handleSave = () => {
      localForm
        .validateFields()
        .then(() => {
          const localValues = localForm.getFieldsValue(
            true,
          ) as ExperienceTranslation;
          if (localValues.is_default && !initialTranslation.is_default) {
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
            commitToParentForm();
            onClose();
          }
        })
        .catch(() => {
          // validation errors shown inline
        });
    };

    useImperativeHandle(ref, () => ({
      save: handleSave,
      isDirty: () => localForm.isFieldsTouched() || !!isOOB,
      getValues: () => localForm.getFieldsValue(true) as ExperienceTranslation,
    }));

    if (translationIndex < 0) {
      return null;
    }

    return (
      <Form
        form={localForm}
        initialValues={initialTranslation}
        layout="vertical"
        key={translation.language}
        onValuesChange={() =>
          onValuesChange?.(
            localForm.getFieldsValue(true) as ExperienceTranslation,
          )
        }
      >
        {isOOB ? (
          <div className="pb-4">
            <OOBTranslationNotice languageName={translation.name} />
          </div>
        ) : null}
        {translationsEnabled && (
          <SwitchField
            name="is_default"
            valuePropName="checked"
            label="Default language"
            switchProps={{
              disabled: Boolean(initialTranslation.is_default),
              "data-testid": `input-translations.${translationIndex}.is_default`,
            }}
          />
        )}

        <Form.Item
          name="title"
          label="Title"
          rules={[{ required: true, message: "Title is required" }]}
          tooltip="Type / to insert a template variable"
        >
          <TemplateVariableInput
            multiline={false}
            required
            variables={GPC_VARIABLES}
            data-testid={`input-translations.${translationIndex}.title`}
          />
        </Form.Item>
        <Form.Item
          name="description"
          label="Description"
          rules={[{ required: true, message: "Description is required" }]}
          tooltip="Type / to insert a template variable"
        >
          <TemplateVariableInput
            required
            variables={DESCRIPTION_VARIABLES}
            data-testid={`input-translations.${translationIndex}.description`}
          />
        </Form.Item>
        {(component === ComponentType.BANNER_AND_MODAL ||
          component === ComponentType.TCF_OVERLAY) && (
          <>
            <Form.Item
              name="banner_title"
              label="Banner title (optional)"
              tooltip="A separate title for the banner (defaults to main title); type / to insert a template variable"
            >
              <TemplateVariableInput
                multiline={false}
                variables={GPC_VARIABLES}
                data-testid={`input-translations.${translationIndex}.banner_title`}
              />
            </Form.Item>
            <Form.Item
              name="banner_description"
              label="Banner description (optional)"
              tooltip="A separate description for the banner (defaults to main description); type / to insert a template variable"
            >
              <TemplateVariableInput
                variables={GPC_VARIABLES}
                data-testid={`input-translations.${translationIndex}.banner_description`}
              />
            </Form.Item>
          </>
        )}
        {component === ComponentType.TCF_OVERLAY && (
          <Form.Item
            name="purpose_header"
            label="Purpose header (optional)"
            tooltip="Appears above the Purpose list section of the TCF banner"
          >
            <Input
              data-testid={`input-translations.${translationIndex}.purpose_header`}
            />
          </Form.Item>
        )}
        <Form.Item
          name="accept_button_label"
          label={`"Accept" button label`}
          rules={[
            { required: true, message: "Accept button label is required" },
          ]}
        >
          <Input
            required
            data-testid={`input-translations.${translationIndex}.accept_button_label`}
          />
        </Form.Item>
        <Form.Item
          name="reject_button_label"
          label={`"Reject" button label`}
          rules={[
            { required: true, message: "Reject button label is required" },
          ]}
        >
          <Input
            required
            data-testid={`input-translations.${translationIndex}.reject_button_label`}
          />
        </Form.Item>
        {formConfig.privacy_preferences_link_label?.included && (
          <Form.Item
            name="privacy_preferences_link_label"
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
            name="save_button_label"
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
            name="acknowledge_button_label"
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
            name="privacy_policy_link_label"
            label="Privacy policy link label (optional)"
          >
            <Input
              data-testid={`input-translations.${translationIndex}.privacy_policy_link_label`}
            />
          </Form.Item>
        )}
        {formConfig.privacy_policy_url?.included && (
          <Form.Item
            name="privacy_policy_url"
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
            name="modal_link_label"
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
            name="gpc_label"
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
            name="gpc_title"
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
            name="gpc_description"
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
            name="gpc_status_applied_label"
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
            name="gpc_status_overridden_label"
            label="GPC 'Overridden' status label (optional)"
            tooltip="Text shown when GPC is overridden (e.g. 'Overridden')"
          >
            <Input
              data-testid={`input-translations.${translationIndex}.gpc_status_overridden_label`}
            />
          </Form.Item>
        )}
      </Form>
    );
  },
);

PrivacyExperienceTranslationForm.displayName =
  "PrivacyExperienceTranslationForm";

export default PrivacyExperienceTranslationForm;
