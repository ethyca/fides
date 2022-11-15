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

interface DeleteProps {
  onDelete: () => void;
  title: string;
  message: ReactNode;
}
interface Props {
  header: string;
  description?: string;
  isOpen: boolean;
  onClose: () => void;
  deleteProps?: DeleteProps;
  children: ReactNode;
  /**
   * Associates the submit button with a form, which is useful for when the button
   * does not live directly inside the form hierarchy
   */
  formId?: string;
  /**
   * Whether or not to include the Cancel and Save buttons
   */
  withFooter?: boolean;
}

const EditDrawer = ({
  header,
  description,
  isOpen,
  onClose,
  deleteProps,
  children,
  formId,
  withFooter = true,
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
            {deleteProps ? (
              <IconButton
                aria-label="delete"
                icon={<TrashCanSolidIcon />}
                size="xs"
                onClick={onDeleteOpen}
                data-testid="delete-btn"
              />
            ) : null}
          </DrawerHeader>
          <DrawerBody>
            {description ? (
              <Text fontSize="sm" mb={4}>
                {description}
              </Text>
            ) : null}
            {children}
          </DrawerBody>
          {withFooter ? (
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
          ) : null}
        </DrawerContent>
      </Drawer>
      {deleteProps ? (
        <ConfirmationModal
          isOpen={deleteIsOpen}
          onClose={onDeleteClose}
          onConfirm={deleteProps.onDelete}
          title={deleteProps.title}
          message={deleteProps.message}
        />
      ) : null}
    </>
  );
};

export default EditDrawer;
