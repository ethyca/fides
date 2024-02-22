import {
  Button,
  ButtonGroup,
  Flex,
  Heading,
  Text,
  useDisclosure,
} from "@fidesui/react";
import { useFormikContext } from "formik";
import { isEqual } from "lodash";
import { useMemo } from "react";

import {
  CustomSwitch,
  CustomTextArea,
  CustomTextInput,
} from "~/features/common/form/inputs";
import WarningModal from "~/features/common/modals/WarningModal";
import { BackButtonNonLink } from "~/features/common/nav/v2/BackButton";
import { TranslationWithLanguageName } from "~/features/privacy-experience/form/helpers";
import { ExperienceConfigCreate, ExperienceTranslation } from "~/types/api";

const PrivacyExperienceTranslationForm = ({
  translation,
  onReturnToMainForm,
}: {
  translation: TranslationWithLanguageName;
  onReturnToMainForm: () => void;
}) => {
  const { values, setFieldValue, errors, touched, setTouched } =
    useFormikContext<ExperienceConfigCreate>();

  // store the initial translation so we can undo changes on discard
  const initialTranslation = useMemo(() => {
    const { name, ...rest } = translation;
    return rest as ExperienceTranslation;
  }, [translation]);

  const translationIndex = values.translations!.findIndex(
    (t) => t.language === translation.language
  );

  const translationIsTouched = !isEqual(
    values.translations![translationIndex],
    initialTranslation
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
    if (initialTranslation.title) {
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
    if (translationIsTouched || !initialTranslation.title) {
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

  return (
    <Flex
      direction="column"
      minH="full"
      w="25%"
      borderRight="1px solid #DEE5EE"
    >
      <Flex direction="column" h="full" overflow="scroll" px={4}>
        <Flex direction="column" gap={4} w="full">
          <BackButtonNonLink onClick={handleLeaveForm} mt={4} />
          <WarningModal
            isOpen={unsavedChangesIsOpen}
            onClose={onCloseUnsavedChanges}
            title="Translation not saved"
            message={
              <Text>
                You have unsaved changes to this translation. Discard changes?
              </Text>
            }
            confirmButtonText="Discard"
            handleConfirm={discardChanges}
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
          <Heading fontSize="md" fontWeight="semibold">
            {translation.name}
          </Heading>
          <CustomSwitch
            name={`translations.${translationIndex}.is_default`}
            id={`translations.${translationIndex}.is_default`}
            label="Default language"
            disabled={initialTranslation.is_default}
            variant="stacked"
          />
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
          <CustomTextInput
            name={`translations.${translationIndex}.privacy_preferences_link_label`}
            id={`translations.${translationIndex}.privacy_preferences_link_label`}
            label={`"Manage privacy preferences" button label`}
            variant="stacked"
          />
          <CustomTextInput
            name={`translations.${translationIndex}.save_button_label`}
            id={`translations.${translationIndex}.save_button_label`}
            label={`"Save" button label`}
            variant="stacked"
          />
          <CustomTextInput
            name={`translations.${translationIndex}.acknowledge_button_label`}
            id={`translations.${translationIndex}.acknowledge_button_label`}
            label={`"Acknowledge" button label`}
            variant="stacked"
          />
          <CustomTextInput
            name={`translations.${translationIndex}.privacy_policy_link_label`}
            id={`translations.${translationIndex}.privacy_policy_link_label`}
            label="Privacy policy link label"
            variant="stacked"
          />
          <CustomTextInput
            name={`translations.${translationIndex}.privacy_policy_url`}
            id={`translations.${translationIndex}.privacy_policy_url`}
            label="Privacy policy link URL"
            variant="stacked"
          />
        </Flex>
      </Flex>
      <ButtonGroup size="sm" borderTop="1px solid #DEE5EE" p={4}>
        <Button variant="outline" onClick={handleLeaveForm}>
          Cancel
        </Button>
        <Button
          colorScheme="primary"
          isDisabled={!translationIsTouched || !!errors.translations}
          data-testid="save-btn"
          onClick={handleSaveTranslation}
        >
          Add translation
        </Button>
      </ButtonGroup>
    </Flex>
  );
};
export default PrivacyExperienceTranslationForm;
