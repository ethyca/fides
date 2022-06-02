import {
  Box,
  Button,
  Drawer,
  DrawerBody,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
  Stack,
  Text,
} from "@fidesui/react";
import { Form, Formik } from "formik";
import { useSelector } from "react-redux";

import { CustomSelect, CustomTextInput } from "../common/form/inputs";
import CloseSolid from "../common/Icon/CloseSolid";
import { DATA_QUALIFIERS } from "./constants";
import {
  selectActiveCollectionIndex,
  selectActiveDataset,
  selectActiveFieldIndex,
  useUpdateDatasetMutation,
} from "./dataset.slice";
import { DatasetField } from "./types";

interface FieldValues {
  description: DatasetField["description"];
  identifiability: DatasetField["data_qualifier"];
  data_categories: DatasetField["data_categories"];
}
interface EditFieldFormProps {
  field: DatasetField;
  onClose: () => void;
}
const EditFieldForm = ({ field, onClose }: EditFieldFormProps) => {
  const initialValues: FieldValues = {
    description: field.description,
    identifiability: field.data_qualifier,
    data_categories: field.data_categories,
  };
  const dataset = useSelector(selectActiveDataset);
  const collectionIndex = useSelector(selectActiveCollectionIndex);
  const fieldIndex = useSelector(selectActiveFieldIndex);
  // const [updateDataset, updateDatasetResult] = useUpdateDatasetMutation();
  const handleSubmit = (values: FieldValues) => {
    console.log({ dataset });
    // merge the updated fields with the original dataset
    if (dataset && collectionIndex != null && fieldIndex != null) {
      const updatedField = { ...field, ...values };
      const updatedDataset = { ...dataset };
      const updatedCollections = [...updatedDataset.collections];
      const updatedFields = [...updatedCollections[collectionIndex].fields];
      updatedFields[fieldIndex] = updatedField;

      console.log({ updatedDataset });
    }
  };
  return (
    <Formik initialValues={initialValues} onSubmit={handleSubmit}>
      <Form>
        <Stack>
          <Box>
            <CustomTextInput name="description" label="Description" />
          </Box>
          <Box>
            <CustomSelect name="identifiability" label="Identifiability">
              {DATA_QUALIFIERS.map((qualifier) => (
                <option key={qualifier.key} value={qualifier.key}>
                  {qualifier.label}
                </option>
              ))}
            </CustomSelect>
          </Box>
          <Box>Data Categories (todo)</Box>
          <Box>
            <Button onClick={onClose} mr={2} size="sm" variant="outline">
              Cancel
            </Button>
            <Button type="submit" colorScheme="primary" size="sm">
              Save
            </Button>
          </Box>
        </Stack>
      </Form>
    </Formik>
  );
};

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
          <Button variant="ghost" onClick={onClose}>
            <CloseSolid />
          </Button>
        </Box>
        <DrawerHeader py={2}>Field Name: {field.name}</DrawerHeader>
        <DrawerBody>
          <Text fontSize="sm" mb={4}>
            By providing a small amount of additional context for each system we
            can make reporting and understanding our tech stack much easier.
          </Text>
          <EditFieldForm field={field} onClose={onClose} />
        </DrawerBody>
      </Box>
    </DrawerContent>
  </Drawer>
);

export default EditFieldDrawer;
