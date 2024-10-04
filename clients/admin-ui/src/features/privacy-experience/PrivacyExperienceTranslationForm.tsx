import { AntButton, Heading, Text, useDisclosure } from "fidesui";
import { useFormikContext } from "formik";
import { isEqual } from "lodash";
import { useMemo } from "react";

import {
  CustomSwitch,
  CustomTextArea,
  CustomTextInput,
} from "~/features/common/form/inputs";
import InfoBox from "~/features/common/InfoBox";
import WarningModal from "~/features/common/modals/WarningModal";
import { BackButtonNonLink } from "~/features/common/nav/v2/BackButton";
import {
  getTranslationFormFields,
  TranslationWithLanguageName,
} from "~/features/privacy-experience/form/helpers";
import { PrivacyExperienceConfigColumnLayout } from "~/features/privacy-experience/PrivacyExperienceForm";
import {
  ComponentType,
  ExperienceConfigCreate,
  ExperienceTranslation,
} from "~/types/api";

export const OOBTranslationNotice = ({
  languageName,
}: {
  languageName: string;
}) => (
  <InfoBox
    text={`This is a default translation provided by Fides. If you've modified the default English language text, these translations will not match, so verify any changes with a native ${languageName} speaker before using.`}
    data-testid="oob-translation-notice"
  />
);

const PrivacyExperienceTranslationForm = ({
  translation,
  translationsEnabled,
  isOOB,
  onReturnToMainForm,
}: {
  translation: TranslationWithLanguageName;
  translationsEnabled?: boolean;
  isOOB?: boolean;
  onReturnToMainForm: () => void;
}) => {
  const { values, setFieldValue, errors, touched, setTouched } =
    useFormikContext<ExperienceConfigCreate>();

  // store the initial translation so we can undo changes on discard
  const initialTranslation = useMemo(() => {
    const { name, ...rest } = translation;
    return rest as ExperienceTranslation;
  }, [translation]);
  const isEditing = !!initialTranslation.title && !isOOB;

  const formConfig = getTranslationFormFields(values.component);

  const translationIndex = values.translations!.findIndex(
    (t) => t.language === translation.language,
  );

  const translationIsTouched = !isEqual(
    values.translations![translationIndex],
    initialTranslation,
  );

  const {
    onOpen: onOpenUnsavedChanges,
    isOpen: unsavedChangesIsOpen,
    onClose: onCloseUnsavedChanges,
  } = useDisclosure();

  const {
    onOpen: onOpenNewDefault,
    isOpen: newDefaultIsOpen,
    onClose: onCloseNewDefault,
  } = useDisclosure();

  const discardChanges = () => {
    const newTranslations = values.translations!.slice();
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
    setFieldValue("translations", newTranslations);
    const { translations, ...rest } = touched;
    setTouched({
      ...rest,
    });
    onReturnToMainForm();
  };

  const handleLeaveForm = () => {
    if (translationIsTouched || isOOB) {
      onOpenUnsavedChanges();
    } else {
      onReturnToMainForm();
    }
  };

  const setNewDefaultTranslation = (newDefaultIndex: number) => {
    const newTranslations = values.translations!.map((t, idx) => ({
      ...t,
      is_default: idx === newDefaultIndex,
    }));
    // move the new default to first in the array
    newTranslations.unshift(newTranslations.splice(newDefaultIndex, 1)[0]);
    setFieldValue("translations", newTranslations);
    onReturnToMainForm();
  };

  const handleSaveTranslation = () => {
    if (
      values.translations![translationIndex].is_default &&
      !initialTranslation.is_default
    ) {
      onOpenNewDefault();
    } else {
      onReturnToMainForm();
    }
  };

  const buttonPanel = (
    <div className="flex justify-between border-t border-[#DEE5EE] p-4">
      <AntButton onClick={handleLeaveForm}>Cancel</AntButton>
      <AntButton
        onClick={handleSaveTranslation}
        type="primary"
        data-testid="save-btn"
        disabled={(!translationIsTouched && !isOOB) || !!errors.translations}
      >
        {isEditing ? "Save" : "Add translation"}
      </AntButton>
    </div>
  );

  let unsavedChangesMessage;
  if (!translationsEnabled) {
    unsavedChangesMessage =
      "You have unsaved changes to this experience text. Discard changes?";
  } else {
    unsavedChangesMessage = isEditing
      ? "You have unsaved changes to this translation. Discard changes?"
      : "This translation has not been added to your experience.  Discard translation?";
  }

  return (
    <PrivacyExperienceConfigColumnLayout buttonPanel={buttonPanel}>
      <BackButtonNonLink onClick={handleLeaveForm} mt={4} />
      <WarningModal
        isOpen={unsavedChangesIsOpen}
        onClose={onCloseUnsavedChanges}
        title={translationsEnabled ? "Translation not saved" : "Text not saved"}
        message={<Text>{unsavedChangesMessage}</Text>}
        confirmButtonText="Discard"
        handleConfirm={discardChanges}
      />
      <Heading fontSize="md" fontWeight="semibold">
        {translationsEnabled
          ? `Edit ${translation.name} translation`
          : "Edit experience text"}
      </Heading>
      {isOOB ? <OOBTranslationNotice languageName={translation.name} /> : null}
      {translationsEnabled && (
        <>
          <CustomSwitch
            name={`translations.${translationIndex}.is_default`}
            id={`translations.${translationIndex}.is_default`}
            label="Default language"
            isDisabled={Boolean(initialTranslation.is_default)}
            variant="stacked"
          />
          <WarningModal
            isOpen={newDefaultIsOpen}
            onClose={onCloseNewDefault}
            title="Update default language"
            message={
              <Text>
                Are you sure you want to update the default language of this
                experience?
              </Text>
            }
            handleConfirm={() => setNewDefaultTranslation(translationIndex)}
          />
        </>
      )}

      <CustomTextInput
        name={`translations.${translationIndex}.title`}
        id={`translations.${translationIndex}.title`}
        label="Title"
        isRequired
        variant="stacked"
      />
      <CustomTextArea
        name={`translations.${translationIndex}.description`}
        id={`translations.${translationIndex}.description`}
        label="Description"
        isRequired
        variant="stacked"
      />
      {(values.component === ComponentType.BANNER_AND_MODAL ||
        values.component === ComponentType.TCF_OVERLAY) && (
        <>
          <CustomTextInput
            name={`translations.${translationIndex}.banner_title`}
            id={`translations.${translationIndex}.banner_title`}
            label="Banner title (optional)"
            tooltip="A separate title for the banner (defaults to main title)"
            variant="stacked"
          />
          <CustomTextArea
            name={`translations.${translationIndex}.banner_description`}
            id={`translations.${translationIndex}.banner_description`}
            label="Banner description (optional)"
            tooltip="A separate description for the banner (defaults to main description)"
            variant="stacked"
          />
        </>
      )}
      {values.component === ComponentType.TCF_OVERLAY && (
        <CustomTextInput
          name={`translations.${translationIndex}.purpose_header`}
          id={`translations.${translationIndex}.purpose_header`}
          label="Purpose header (optional)"
          tooltip="Appears above the Purpose list section of the TCF banner"
          variant="stacked"
        />
      )}
      <CustomTextInput
        name={`translations.${translationIndex}.accept_button_label`}
        id={`translations.${translationIndex}.accept_button_label`}
        label={`"Accept" button label`}
        isRequired
        variant="stacked"
      />
      <CustomTextInput
        name={`translations.${translationIndex}.reject_button_label`}
        id={`translations.${translationIndex}.reject_button_label`}
        label={`"Reject" button label`}
        isRequired
        variant="stacked"
      />
      {formConfig.privacy_preferences_link_label?.included && (
        <CustomTextInput
          name={`translations.${translationIndex}.privacy_preferences_link_label`}
          id={`translations.${translationIndex}.privacy_preferences_link_label`}
          label={`"Manage privacy preferences" button label`}
          variant="stacked"
          isRequired={formConfig.privacy_preferences_link_label?.required}
        />
      )}
      {formConfig.save_button_label?.included && (
        <CustomTextInput
          name={`translations.${translationIndex}.save_button_label`}
          id={`translations.${translationIndex}.save_button_label`}
          label={`"Save" button label`}
          variant="stacked"
          isRequired={formConfig.save_button_label.required}
        />
      )}
      {formConfig.acknowledge_button_label?.included && (
        <CustomTextInput
          name={`translations.${translationIndex}.acknowledge_button_label`}
          id={`translations.${translationIndex}.acknowledge_button_label`}
          label={`"Acknowledge" button label`}
          variant="stacked"
          isRequired={formConfig.acknowledge_button_label.required}
        />
      )}
      {formConfig.privacy_policy_link_label?.included && (
        <CustomTextInput
          name={`translations.${translationIndex}.privacy_policy_link_label`}
          id={`translations.${translationIndex}.privacy_policy_link_label`}
          label="Privacy policy link label (optional)"
          variant="stacked"
        />
      )}
      {formConfig.privacy_policy_url?.included && (
        <CustomTextInput
          name={`translations.${translationIndex}.privacy_policy_url`}
          id={`translations.${translationIndex}.privacy_policy_url`}
          label="Privacy policy link URL (optional)"
          variant="stacked"
        />
      )}
      {formConfig.modal_link_label?.included && (
        <CustomTextInput
          name={`translations.${translationIndex}.modal_link_label`}
          id={`translations.${translationIndex}.modal_link_label`}
          label="Trigger link label (optional)"
          tooltip="Include text here if you would like the Fides CMP to manage the copy of the button that is included on your site to open the CMP."
          variant="stacked"
        />
      )}
    </PrivacyExperienceConfigColumnLayout>
  );
};
export default PrivacyExperienceTranslationForm;
