import {
  AntButton as Button,
  Box,
  BoxProps,
  EditIcon,
  Text,
  useDisclosure,
  WarningIcon,
} from "fidesui";

import { TrashCanOutlineIcon } from "~/features/common/Icon/TrashCanOutlineIcon";
import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import { CustomFieldDefinitionWithId } from "~/types/api";

interface CustomFieldActionsProps extends BoxProps {
  customField: CustomFieldDefinitionWithId;
  onEdit: (
    customField: CustomFieldDefinitionWithId,
    e: React.MouseEvent<HTMLButtonElement, MouseEvent>,
  ) => void;
  onDelete: (customField: CustomFieldDefinitionWithId) => void;
}

export const CustomFieldActions = ({
  customField,
  onEdit,
  onDelete,
  ...props
}: CustomFieldActionsProps): JSX.Element => {
  const modal = useDisclosure();
  return (
    <Box {...props}>
      <Button
        aria-label="Edit property"
        data-testid="edit-property-button"
        size="small"
        className="mr-[10px]"
        icon={<EditIcon />}
        onClick={(e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
          e.stopPropagation();
          onEdit(customField, e);
        }}
      />
      <Button
        aria-label="Delete property"
        data-testid="delete-property-button"
        size="small"
        className="mr-[10px]"
        icon={<TrashCanOutlineIcon />}
        onClick={(e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
          e.stopPropagation();
          modal.onOpen();
        }}
      />

      <ConfirmationModal
        isOpen={modal.isOpen}
        onClose={modal.onClose}
        onConfirm={() => {
          onDelete(customField);
          modal.onClose();
        }}
        title="Delete custom field"
        message={
          <Text color="gray.500">
            Are you sure you want to delete this custom field? This will remove
            the custom field and all stored values and this action can&apos;t be
            undone.
          </Text>
        }
        continueButtonText="Confirm"
        isCentered
        icon={<WarningIcon />}
      />
    </Box>
  );
};
