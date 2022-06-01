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
import { ErrorMessage, Field, Form, Formik } from "formik";

import CloseSolid from "../common/Icon/CloseSolid";
import { DatasetField } from "./types";

interface FieldValues {
  description: DatasetField["description"];
  identifiability: DatasetField["data_qualifier"];
  data_categories: DatasetField["data_categories"];
}
const EditFieldForm = ({ field }: { field: DatasetField }) => {
  const initialValues: FieldValues = {
    description: field.description,
    identifiability: field.data_qualifier,
    data_categories: field.data_categories,
  };
  const handleSubmit = (values: FieldValues) => {
    console.log("submitting!", values);
  };
  return (
    <Formik initialValues={initialValues} onSubmit={handleSubmit}>
      <Form>
        <Stack>
          <Box>
            <label htmlFor="description">Description</label>
            <Field name="description" type="text" className="form-input" />
            <ErrorMessage name="description" />
          </Box>
          <Box>
            <label htmlFor="identifiability">Identifiability</label>
            <Field name="identifiability" type="text" className="form-input" />
            <ErrorMessage name="identifiability" />
          </Box>
          <Box>
            <label htmlFor="data_categories">Data Categories</label>
            <Field name="data_categories" type="text" className="form-input" />
            <ErrorMessage name="data_categories" />
          </Box>
        </Stack>

        <Button type="submit">Save</Button>
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
          <EditFieldForm field={field} />
        </DrawerBody>
      </Box>
    </DrawerContent>
  </Drawer>
);

export default EditFieldDrawer;
