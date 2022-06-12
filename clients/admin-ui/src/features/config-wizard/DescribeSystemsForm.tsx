import {
  Button,
  chakra,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Stack,
} from "@fidesui/react";
import { useFormik } from "formik";
import type { NextPage } from "next";
import React, { useState } from "react";

//   import { QuestionIcon } from "~/features/common/Icon";

//   import { useCreateOrganizationMutation } from "./organization.slice";

const useDescribeSystemsForm = (handleChangeStep: Function) => {
  // const [createOrganization] = useCreateOrganizationMutation();
  const [isLoading, setIsLoading] = useState(false);
  // const toast = useToast();
  const formik = useFormik({
    initialValues: {
      name: "",
      key: "",
      description: "",
      type: "",
      tags: [],
    },
    onSubmit: async (values) => {
      // const systemBody = {
      //   name: values.name,
      //   key: values.key,
      //   description: values.description,
      //   type: values.type,
      //   tags: values.tags,
      // };
      setIsLoading(true);

      // @ts-ignore
      // const { error: createSystemError } =
      // await createOrganization(
      //   systemBody
      // );

      setIsLoading(false);

      // if (createSystemError) {
      //   toast({
      //     status: "error",
      //     description: "Creating system failed.",
      //   });
      // } else {
      //   handleChangeStep(...);
      //   toast.closeAll();
      // }
    },
    validate: (values) => {
      const errors: {
        name?: string;
        key?: string;
        description?: string;
        type?: string;
        tags?: string[];
      } = {};

      if (!values.name) {
        errors.name = "System name is required";
      }

      if (!values.key) {
        errors.key = "System key is equired";
      }

      if (!values.description) {
        errors.description = "System description is equired";
      }

      if (!values.type) {
        errors.type = "System type is required";
      }

      return errors;
    },
  });

  return { ...formik, isLoading };
};

const DescribeSystemsForm: NextPage<{
  handleChangeStep: Function;
}> = ({ handleChangeStep }) => {
  const {
    errors,
    handleBlur,
    handleChange,
    handleSubmit,
    isLoading,
    touched,
    values,
  } = useDescribeSystemsForm(handleChangeStep);

  return (
    <chakra.form onSubmit={handleSubmit}>
      <Stack ml="50px" spacing="24px" w="80%">
        <Heading as="h3" size="lg">
          {/* If describing system manually */}
          Describe your system
        </Heading>
        <div>
          By providing a small amount of additional context for each system we
          can make reporting and understanding our tech stack much easier for
          everyone from engineering to legal teams. So let’s do this now.
        </div>
        <Stack>
          <FormControl>
            <Stack direction="row" mb={5} justifyContent="flex-end">
              <FormLabel w="100%">System name</FormLabel>
              <Input
                type="text"
                id="name"
                name="name"
                focusBorderColor="gray.700"
                onChange={handleChange}
                onBlur={handleBlur}
                value={values.name}
                isInvalid={touched.name && Boolean(errors.name)}
                minW="65%"
                w="65%"
              />
              {/* <Tooltip
                  fontSize="md"
                  label="The legal name of your organization"
                  placement="right"
                >
                  <QuestionIcon boxSize={5} color="gray.400" />
                </Tooltip> */}
            </Stack>
            <Stack direction="row" justifyContent="flex-end">
              <FormLabel w="100%">System key</FormLabel>
              <Input
                type="text"
                id="key"
                name="key"
                focusBorderColor="gray.700"
                onChange={handleChange}
                onBlur={handleBlur}
                value={values.key}
                isInvalid={touched.key && Boolean(errors.key)}
                minW="65%"
                w="65%"
              />
              {/* <Tooltip
                  fontSize="md"
                  label="An explanation of the type of organization and primary activity. 
                    For example “Acme Inc. is an e-commerce company that sells scarves.”"
                  placement="right"
                >
                  <QuestionIcon boxSize={5} color="gray.400" />
                </Tooltip> */}
            </Stack>
            <Stack direction="row" justifyContent="flex-end">
              <FormLabel w="100%">Description</FormLabel>
              <Input
                type="text"
                id="description"
                name="description"
                focusBorderColor="gray.700"
                onChange={handleChange}
                onBlur={handleBlur}
                value={values.description}
                isInvalid={touched.description && Boolean(errors.description)}
                minW="65%"
                w="65%"
              />
              {/* <Tooltip
                  fontSize="md"
                  label="An explanation of the type of organization and primary activity. 
                    For example “Acme Inc. is an e-commerce company that sells scarves.”"
                  placement="right"
                >
                  <QuestionIcon boxSize={5} color="gray.400" />
                </Tooltip> */}
            </Stack>
          </FormControl>
        </Stack>
        <Button
          bg="primary.800"
          _hover={{ bg: "primary.400" }}
          _active={{ bg: "primary.500" }}
          colorScheme="primary"
          disabled={!values.name || !values.description}
          isLoading={isLoading}
          type="submit"
        >
          Confirm and Continue
        </Button>
      </Stack>
    </chakra.form>
  );
};
export default DescribeSystemsForm;
