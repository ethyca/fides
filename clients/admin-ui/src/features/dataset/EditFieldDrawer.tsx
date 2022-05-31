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

import CloseSolid from "../common/Icon/CloseSolid";
import { DatasetField } from "./types";

interface Props {
  field: DatasetField;
  isOpen: boolean;
  onClose: () => void;
}

const EditFieldDrawer = ({ field, isOpen, onClose }: Props) => (
  <Drawer placement="right" isOpen={isOpen} onClose={onClose} size="md">
    <DrawerOverlay />
    <DrawerContent>
      <Box py={2}>
        <Box display="flex" justifyContent="flex-end" mr={2}>
          <Button variant="ghost">
            <CloseSolid />
          </Button>
        </Box>
        <DrawerHeader py={2}>Field Name: {field.name}</DrawerHeader>
        <DrawerBody>
          <Text fontSize="sm">
            By providing a small amount of additional context for each system we
            can make reporting and understanding our tech stack much easier.
          </Text>
        </DrawerBody>
      </Box>
    </DrawerContent>
  </Drawer>
);

export default EditFieldDrawer;
