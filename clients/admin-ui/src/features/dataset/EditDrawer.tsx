import {
  Box,
  Button,
  Drawer,
  DrawerBody,
  DrawerContent,
  DrawerFooter,
  DrawerHeader,
  DrawerOverlay,
  IconButton,
  Text,
  useDisclosure,
} from "@fidesui/react";
import ConfirmationModal from "common/ConfirmationModal";
import { ReactNode } from "react";

import { CloseSolidIcon, TrashCanSolidIcon } from "~/features/common/Icon";

interface Props {
  header: string;
  description: string;
  isOpen: boolean;
  onClose: () => void;
  onDelete: () => void;
  deleteTitle: string;
  deleteMessage: ReactNode;
  children: ReactNode;
  /* Associates the submit button with a form, which is useful for when the button
   * does not live directly inside the form hierarchy
   */
  formId?: string;
}

const EditDrawer = ({
  header,
  description,
  isOpen,
  onClose,
  onDelete,
  deleteTitle,
  deleteMessage,
  children,
  formId,
}: Props) => {
  const {
    isOpen: deleteIsOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();

  return (
    <>
      <Drawer placement="right" isOpen={isOpen} onClose={onClose} size="lg">
        <DrawerOverlay />
        <DrawerContent data-testid="edit-drawer-content" py={2}>
          <Box display="flex" justifyContent="flex-end" mr={2}>
            <Button variant="ghost" onClick={onClose}>
              <CloseSolidIcon />
            </Button>
          </Box>
          <DrawerHeader py={2} display="flex" alignItems="center">
            <Text mr="2">{header}</Text>
            <IconButton
              aria-label="delete"
              icon={<TrashCanSolidIcon />}
              size="xs"
              onClick={onDeleteOpen}
              data-testid="delete-btn"
            />
          </DrawerHeader>
          <DrawerBody>
            <Text fontSize="sm" mb={4}>
              {description}
            </Text>
            {children}
          </DrawerBody>
          <DrawerFooter justifyContent="flex-start">
            <Button onClick={onClose} mr={2} size="sm" variant="outline">
              Cancel
            </Button>
            <Button
              type="submit"
              colorScheme="primary"
              size="sm"
              data-testid="save-btn"
              form={formId}
            >
              Save
            </Button>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>
      <ConfirmationModal
        isOpen={deleteIsOpen}
        onClose={onDeleteClose}
        onConfirm={onDelete}
        title={deleteTitle}
        message={deleteMessage}
      />
    </>
  );
};

export default EditDrawer;
