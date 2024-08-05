import {
  Box,
  Button,
  CloseIcon,
  Drawer,
  DrawerBody,
  DrawerContent,
  DrawerFooter,
  DrawerHeader,
  DrawerOverlay,
  IconButton,
  Text,
} from "fidesui";
import { ReactNode } from "react";

import { TrashCanOutlineIcon } from "~/features/common/Icon/TrashCanOutlineIcon";

interface Props {
  header?: ReactNode;
  description?: string;
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
}

export const EditDrawerHeader = ({
  title,
  onDelete,
}: {
  title: string;
  onDelete?: () => void;
}) => (
  <DrawerHeader py={0} display="flex" alignItems="flex-start">
    <Text mr="2" color="gray.700" fontSize="lg" lineHeight={1.8}>
      {title}
    </Text>
    {onDelete ? (
      <IconButton
        variant="outline"
        aria-label="delete"
        icon={<TrashCanOutlineIcon fontSize="small" />}
        size="sm"
        onClick={onDelete}
        data-testid="delete-btn"
      />
    ) : null}
  </DrawerHeader>
);

export const EditDrawerFooter = ({
  onClose,
  formId,
  isSaving,
}: {
  /**
   * Associates the submit button with a form, which is useful for when the button
   * does not live directly inside the form hierarchy
   */
  formId?: string;
  isSaving?: boolean;
} & Pick<Props, "onClose">) => (
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
      isLoading={isSaving}
    >
      Save
    </Button>
  </DrawerFooter>
);

const EditDrawer = ({
  header,
  description,
  isOpen,
  onClose,
  children,
  footer,
}: Props) => (
  <Drawer placement="right" isOpen={isOpen} onClose={onClose} size="md">
    <DrawerOverlay />
    <DrawerContent data-testid="edit-drawer-content" py={2}>
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="top"
        mr={2}
        py={2}
        gap={2}
      >
        <Box flex={1} minH={8}>
          {header}
        </Box>
        <Box display="flex" justifyContent="flex-end" mr={2}>
          <IconButton
            aria-label="Close editor"
            variant="outline"
            onClick={onClose}
            data-testid="close-drawer-btn"
            size="sm"
            icon={<CloseIcon fontSize="smaller" />}
          />
        </Box>
      </Box>

      <DrawerBody pt={1}>
        {description ? (
          <Text fontSize="sm" mb={4} color="gray.600">
            {description}
          </Text>
        ) : null}
        {children}
      </DrawerBody>
      {footer}
    </DrawerContent>
  </Drawer>
);

export default EditDrawer;
