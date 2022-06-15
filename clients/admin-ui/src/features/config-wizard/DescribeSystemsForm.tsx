import {
  Button,
  chakra,
  FormControl,
  FormLabel,
  Heading,
  HStack,
  Input,
  Select,
  Stack,
  Tooltip,
} from "@fidesui/react";
import { ChakraStylesConfig, CreatableSelect } from "chakra-react-select";
import { useFormik } from "formik";
import type { NextPage } from "next";
import React, { useState } from "react";
import { QuestionIcon } from "~/features/common/Icon";

//   import { useCreateOrganizationMutation } from "./organization.slice";

const useDescribeSystemsForm = () =>
  // handleChangeStep: Function
  {
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
      onSubmit: async () =>
        // values
        {
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
}> = () =>
  //   {
  // handleChangeStep
  //   }
  {
    const {
      errors,
      handleBlur,
      handleChange,
      handleSubmit,
      isLoading,
      touched,
      values,
    } = useDescribeSystemsForm();
    //   handleChangeStep

    const chakraStyles: ChakraStylesConfig = {
      multiValue: (provided, state) => ({
        ...provided,
        background: "primary.400",
        color: "white",
      }),
      multiValueRemove: (provided, state) => ({
        ...provided,
        display: "none",
        visibility: "hidden",
      }),
    };

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
              <Stack direction="row" mb={5}>
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
                <Tooltip
                  fontSize="md"
                  label="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
                  placement="right"
                >
                  <QuestionIcon boxSize={5} color="gray.400" />
                </Tooltip>
              </Stack>
              <Stack direction="row">
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
                <Tooltip
                  fontSize="md"
                  label="System key’s are automatically generated from the resource id and system name to provide a unique key for identifying systems in the registry."
                  placement="right"
                >
                  <QuestionIcon boxSize={5} color="gray.400" />
                </Tooltip>
              </Stack>
              <Stack direction="row">
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
                <Tooltip
                  fontSize="md"
                  label="If you wish you can provide a description which better explains the purpose of this system."
                  placement="right"
                >
                  <QuestionIcon boxSize={5} color="gray.400" />
                </Tooltip>
              </Stack>
              <Stack direction="row">
                <FormLabel>System type</FormLabel>
                <Select placeholder="Select option">
                  <option value="emailSystem">Email System</option>
                  <option value="option2">Option 2</option>
                  <option value="option3">Option 3</option>
                </Select>
                <Tooltip
                  fontSize="md"
                  label="Select a system type from the pre-approved list of system types."
                  placement="right"
                >
                  <QuestionIcon boxSize={5} color="gray.400" />
                </Tooltip>
              </Stack>
            </FormControl>
          </Stack>
          <Stack>
            <HStack direction="row" spacing={4}>
              <FormLabel>System tags</FormLabel>
              <FormControl>
                <CreatableSelect
                  isMulti
                  isClearable
                  noOptionsMessage={() => null}
                  placeholder="Add your system tags"
                  components={{
                    Menu: () => null,
                    DropdownIndicator: () => null,
                  }}
                  chakraStyles={chakraStyles}
                  size="md"
                />
              </FormControl>
              <Tooltip
                fontSize="md"
                label="Provide one or more tags to group the system. Tags are important as they allow you to filter and group systems for reporting and later review. Tags provide tremendous value as you scale - imagine you have thousands of systems, you’re going to thank us later for tagging!"
                placement="right"
              >
                <QuestionIcon boxSize={5} color="gray.400" />
              </Tooltip>
            </HStack>
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
