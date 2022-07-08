import { Box, Button, Text } from "@fidesui/react";
import { Form, Formik } from "formik";
import * as Yup from "yup";

import { CustomTextInput } from "../common/form/inputs";

const initialValues = { url: "" };

const ValidationSchema = Yup.object().shape({
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
          <Box mb={8}>
            <CustomTextInput name="url" label="Database URL" />
          </Box>
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
