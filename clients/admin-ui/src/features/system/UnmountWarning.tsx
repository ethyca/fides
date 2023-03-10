import { Text, useDisclosure } from "@fidesui/react";
import { useFormikContext } from "formik";
import { useEffect } from "react";

import ConfirmationModal from "~/features/common/ConfirmationModal";

/**
 * Renders a confirmation modal if it detects the parent form has a dirty state
 * and it is unmounting
 */
const UnmountWarning = ({
  isUnmounting,
  onContinue,
  onCancel,
}: {
  isUnmounting: boolean;
  onContinue: () => void;
  onCancel: () => void;
}) => {
  const { dirty } = useFormikContext();
  const { isOpen, onClose, onOpen } = useDisclosure();

  useEffect(() => {
    if (isUnmounting && dirty) {
      onOpen();
    } else {
      onContinue();
    }
  }, [isUnmounting, dirty, onOpen, onContinue]);

  const handleCancel = () => {
    onCancel();
    onClose();
  };

  return (
    <ConfirmationModal
      cancelButtonText="Continue editing"
      continueButtonText="Discard"
      isCentered
      isOpen={isOpen}
      onClose={handleCancel}
      onConfirm={onContinue}
      title="Unsaved changes"
      message={
        <Text color="gray.500">
          You have unsaved changes, are you sure you want to discard?
        </Text>
      }
    />
  );
};

export default UnmountWarning;
