import {
  Box,
  Button,
  Drawer,
  DrawerBody,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
  Text,
} from "@fidesui/react";
import { ReactNode } from "react";

import { CloseSolidIcon } from "~/features/common/Icon";

interface Props {
  header: string;
  description: string;
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
}

const EditDrawer = ({
  header,
  description,
  isOpen,
  onClose,
  children,
}: Props) => (
  <Drawer placement="right" isOpen={isOpen} onClose={onClose} size="md">
    <DrawerOverlay />
    <DrawerContent>
      <Box py={2}>
        <Box display="flex" justifyContent="flex-end" mr={2}>
          <Button variant="ghost" onClick={onClose}>
            <CloseSolidIcon />
          </Button>
        </Box>
        <DrawerHeader py={2}>{header}</DrawerHeader>
        <DrawerBody>
          <Text fontSize="sm" mb={4}>
            {description}
          </Text>
          {children}
        </DrawerBody>
      </Box>
    </DrawerContent>
  </Drawer>
);

export default EditDrawer;
