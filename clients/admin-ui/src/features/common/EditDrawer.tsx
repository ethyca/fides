import {
  AntButton,
  Box,
  CloseIcon,
  Drawer,
  DrawerBody,
  DrawerContent,
  DrawerFooter,
  DrawerHeader,
  DrawerOverlay,
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

export const EditDrawerHeader = ({ title }: { title: string }) => (
  <DrawerHeader py={0} display="flex" alignItems="flex-start">
    <Text mr="2" color="gray.700" fontSize="lg" lineHeight={1.8}>
      {title}
    </Text>
  </DrawerHeader>
);

export const EditDrawerFooter = ({
  onDelete,
  onEditYaml,
  formId,
  isSaving,
}: {
  /**
   * Associates the submit button with a form, which is useful for when the button
   * does not live directly inside the form hierarchy
   */
  formId?: string;
  isSaving?: boolean;
  onDelete?: () => void;
  onEditYaml?: () => void;
} & Pick<Props, "onClose">) => (
  <DrawerFooter justifyContent="space-between">
    {onDelete ? (
      <AntButton
        aria-label="delete"
        icon={<TrashCanOutlineIcon fontSize="small" />}
        onClick={onDelete}
        data-testid="delete-btn"
      />
    ) : null}
    <div className="flex gap-2">
      {onEditYaml && (
        <AntButton onClick={onEditYaml} data-testid="edit-yaml-btn">
          Edit YAML
        </AntButton>
      )}
      <AntButton
        htmlType="submit"
        type="primary"
        data-testid="save-btn"
        form={formId}
        loading={isSaving}
      >
        Save
      </AntButton>
    </div>
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
          <AntButton
            aria-label="Close editor"
            onClick={onClose}
            data-testid="close-drawer-btn"
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
