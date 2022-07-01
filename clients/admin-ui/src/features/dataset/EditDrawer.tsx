import {
  Box,
  Button,
  Drawer,
  DrawerBody,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
  IconButton,
  Text,
  useDisclosure,
} from "@fidesui/react";
import { ReactNode } from "react";

import { CloseSolidIcon, TrashCanSolidIcon } from "~/features/common/Icon";

import ConfirmationModal from "../common/ConfirmationModal";

interface Props {
  header: string;
  description: string;
  isOpen: boolean;
  onClose: () => void;
  onDelete: () => void;
  deleteTitle: string;
  deleteMessage: ReactNode;
  children: ReactNode;
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
        <DrawerContent>
          <Box py={2}>
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
              />
            </DrawerHeader>
            <DrawerBody>
              <Text fontSize="sm" mb={4}>
                {description}
              </Text>
              {children}
            </DrawerBody>
          </Box>
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
