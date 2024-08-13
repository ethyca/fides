import {
  Box,
  Button,
  CloseSolidIcon,
  Drawer,
  DrawerBody,
  DrawerContent,
  DrawerFooter,
  DrawerHeader,
  DrawerOverlay,
  IconButton,
  Text,
  TrashCanSolidIcon,
} from "fidesui";
import { ReactNode } from "react";

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
  <DrawerHeader py={2} display="flex" alignItems="center">
    <Text mr="2">{title}</Text>
    {onDelete ? (
      <IconButton
        aria-label="delete"
        icon={<TrashCanSolidIcon />}
        size="xs"
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
  <Drawer placement="right" isOpen={isOpen} onClose={onClose} size="lg">
    <DrawerOverlay />
    <DrawerContent data-testid="edit-drawer-content" py={2}>
      <Box display="flex" justifyContent="flex-end" mr={2}>
        <Button
          variant="ghost"
          onClick={onClose}
          data-testid="close-drawer-btn"
        >
          <CloseSolidIcon width="17px" />
        </Button>
      </Box>
      {header}
      <DrawerBody>
        {description ? (
          <Text fontSize="sm" mb={4}>
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
