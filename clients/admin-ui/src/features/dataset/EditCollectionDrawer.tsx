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

import { CloseSolidIcon } from "~/features/common/Icon";

import { DatasetCollection } from "./types";

interface Props {
  collection: DatasetCollection;
  isOpen: boolean;
  onClose: () => void;
}
const EditCollectionDrawer = ({ collection, isOpen, onClose }: Props) => (
  <Drawer placement="right" isOpen={isOpen} onClose={onClose} size="md">
    <DrawerOverlay />
    <DrawerContent>
      <Box py={2}>
        <Box display="flex" justifyContent="flex-end" mr={2}>
          <Button variant="ghost" onClick={onClose}>
            <CloseSolidIcon />
          </Button>
        </Box>
        <DrawerHeader py={2}>Collection Name: {collection.name}</DrawerHeader>
        <DrawerBody>
          <Text fontSize="sm" mb={4}>
            By providing a small amount of additional context for each system we
            can make reporting and understanding our tech stack much easier.
          </Text>
          {/* <EditFieldForm field={field} onClose={onClose} /> */}
        </DrawerBody>
      </Box>
    </DrawerContent>
  </Drawer>
);

export default EditCollectionDrawer;
