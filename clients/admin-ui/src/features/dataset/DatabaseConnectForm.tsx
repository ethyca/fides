import { Button, Stack, Text } from "@fidesui/react";
import { Form, Formik } from "formik";
import * as Yup from "yup";

import { CustomSelect, CustomTextInput } from "../common/form/inputs";
import { DATABASE_OPTIONS } from "./constants";

const initialValues = { type: "", url: "" };

const ValidationSchema = Yup.object().shape({
  type: Yup.string().required().label("Database type"),
  url: Yup.string().required().label("Database URL"),
});

const DatabaseConnectForm = () => {
  const handleCreate = () => {
    //   TODO when backend supports this (829)
  };

  return (
    <Formik
      initialValues={initialValues}
      validationSchema={ValidationSchema}
      onSubmit={handleCreate}
      validateOnChange={false}
      validateOnBlur={false}
    >
      {({ isSubmitting }) => (
        <Form>
          <Text size="sm" color="gray.700" mb={8}>
            Connect to one of your databases using a connection URL. You may
            have received this URL from a colleague or your Ethyca developer
            support engineer.
          </Text>
          <Stack mb={8} spacing={4}>
            <CustomSelect
              name="type"
              label="Database type"
              options={DATABASE_OPTIONS}
            />
            <CustomTextInput name="url" label="Database URL" />
          </Stack>
          <Button
            size="sm"
            colorScheme="primary"
            type="submit"
            disabled={isSubmitting}
          >
            Create dataset
          </Button>
        </Form>
      )}
    </Formik>
  );
};

export default DatabaseConnectForm;
