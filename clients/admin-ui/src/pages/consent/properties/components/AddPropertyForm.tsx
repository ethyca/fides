import { Box, Button, Flex } from "@fidesui/react";
import { Form, Formik } from "formik";

import FormSection from "~/features/common/form/FormSection";

const AddPropertyForm = () => (
    <Formik initialValues={[]} onSubmit={() => {}}>
      {() => (
        <Form
          style={{
            paddingTop: "12px",
            paddingBottom: "12px",
          }}
        >
          <Box py={3}>
            <FormSection title="Property details" />
          </Box>
          <Box py={3}>
            <FormSection title="Experiences" />
          </Box>
          <Box py={3}>
            <FormSection title="Advanced settings" />
          </Box>
          <Flex justifyContent="right" width="100%" paddingTop={2}>
            <Button
              size="sm"
              type="submit"
              colorScheme="primary"
              isLoading={false}
            >
              Save
            </Button>
          </Flex>
        </Form>
      )}
    </Formik>
  );

export default AddPropertyForm;
