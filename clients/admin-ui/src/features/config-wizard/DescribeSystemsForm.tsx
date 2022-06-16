import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Heading,
  Input,
  SimpleGrid,
  Stack,
  Tooltip,
  useToast,
} from "@fidesui/react";
import { ChakraStylesConfig, CreatableSelect } from "chakra-react-select";
import {
  FieldHookConfig,
  Form,
  Formik,
  useField,
  useFormik,
  useFormikContext,
} from "formik";
import type { NextPage } from "next";
import React, { useState } from "react";
import { QuestionIcon } from "~/features/common/Icon";
import HorizontalStepper from "../common/HorizontalStepper";
import {
  useCreateSystemMutation,
  useGetSystemByFidesKeyQuery,
  useUpdateSystemMutation,
} from "../system";
// TODO: are we creating/updating just a system here
// and/or do we need to also update the organization itself?
import { HORIZONTALSTEPS } from "./constants";
interface Option {
  value: string;
  label: string;
}

interface SelectProps {
  label: string;
  options: Option[];
  isSearchable?: boolean;
  isClearable?: boolean;
}

export const CustomCreatableMultiSelect = ({
  label,
  options,
  isSearchable,
  isClearable,
  ...props
}: SelectProps & FieldHookConfig<string[]>) => {
  const [field, meta] = useField(props);
  const isInvalid = !!(meta.touched && meta.error);
  const selected = options.filter((o) => field.value.indexOf(o.value) >= 0);
  // note: for Multiselect we have to do setFieldValue instead of field.onChange
  // because field.onChange only accepts strings or events right now, not string[]
  // https://github.com/jaredpalmer/formik/issues/1667
  const { setFieldValue } = useFormikContext();

  return (
    <FormControl>
      <SimpleGrid columns={[1, 2]}>
        <FormLabel htmlFor={props.id || props.name} size="sm">
          {label}
        </FormLabel>
        <CreatableSelect
          options={options}
          onBlur={(option) => {
            if (option) {
              field.onBlur(props.name);
            }
          }}
          onChange={(newValue) => {
            setFieldValue(
              field.name,
              newValue.map((v) => v.value)
            );
          }}
          name={props.name}
          // value={selected}
          size="sm"
          chakraStyles={{
            dropdownIndicator: (provided) => ({
              ...provided,
              bg: "transparent",
              px: 2,
              cursor: "inherit",
            }),
            indicatorSeparator: (provided) => ({
              ...provided,
              display: "none",
            }),
          }}
          isClearable={isClearable}
          isMulti
        />
      </SimpleGrid>
      {/* {isInvalid ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null} */}
    </FormControl>
  );
};

const useDescribeSystemsForm = (
  handleChangeStep: Function,
  fidesKey: string
) => {
  const [updateSystem] = useUpdateSystemMutation();
  const [createSystem] = useCreateSystemMutation();
  const [isLoading, setIsLoading] = useState(false);
  // TODO: Need a way to check for an existing fides key from the start of the wizard
  // const { data: existingSystem } = useGetSystemByFidesKeyQuery(fidesKey)
  const { data: existingSystem } = useGetSystemByFidesKeyQuery(
    "default_organization"
  );

  const toast = useToast();
  const formik = useFormik({
    initialValues: {
      name: existingSystem?.name ?? "",
      key: "",
      // TODO: is key stored? not seeing it in system info
      description: existingSystem?.description ?? "",
      type: existingSystem?.system_type ?? "",
      tags: existingSystem?.system_dependencies ?? [],
      // TODO: double-check that these are tags = system_dependencies ?
    },
    onSubmit: async (values) => {
      const systemBody = {
        fides_key: existingSystem?.fides_key ?? "default_organization",
        name: values.name ?? existingSystem?.name,
        key: values.key,
        // TODO: is key stored? not seeing it in system info
        description: values.description ?? existingSystem?.description,
        type: values.type ?? existingSystem?.system_type,
        tags: values.tags ?? existingSystem?.system_dependencies,
        // TODO: double-check that these are tags = system_dependencies ?
      };
      // TODO: Need to check with this body that if they have a fides_key assigned,
      // then assign that existing one

      console.log("system body", systemBody);

      setIsLoading(true);

      if (!existingSystem) {
        // @ts-ignore
        const { error: createSystemError } = await createSystem(systemBody);

        if (createSystemError) {
          toast({
            status: "error",
            description: "Creating system failed.",
          });
        } else {
          toast.closeAll();
          handleChangeStep(5);
        }
      } else {
        // @ts-ignore
        const { error: updateSystemError } = await updateSystem(systemBody);

        if (updateSystemError) {
          toast({
            status: "error",
            description: "Updating system failed.",
          });
        } else {
          toast.closeAll();
          handleChangeStep(5);
        }
      }

      setIsLoading(false);
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

  return { ...formik, existingSystem, isLoading };
};

const DescribeSystemsForm: NextPage<{
  fidesKey: string;
  handleChangeStep: Function;
  handleCancelSetup: Function;
}> = ({ fidesKey, handleChangeStep, handleCancelSetup }) => {
  const {
    errors,
    handleBlur,
    handleChange,
    handleSubmit,
    isLoading,
    touched,
    values,
    existingSystem,
    initialValues,
  } = useDescribeSystemsForm(handleChangeStep, fidesKey);

  const chakraStyles: ChakraStylesConfig = {
    container: (provided, state) => ({
      ...provided,
      width: "65%",
      maxWidth: "65%",
    }),
    dropdownIndicator: (provided, state) => ({
      ...provided,
      background: "white",
    }),
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

  const handleSubmitTest = async (values: any) => {
    const systemBody = {
      fides_key: existingSystem?.fides_key ?? "default_organization",
      name: values.name ?? existingSystem?.name,
      key: values.key,
      // TODO: is key stored? not seeing it in system info
      description: values.description ?? existingSystem?.description,
      type: values.type ?? existingSystem?.system_type,
      tags: values.tags ?? existingSystem?.system_dependencies,
      // TODO: double-check that these are tags = system_dependencies ?
    };
    // TODO: Need to check with this body that if they have a fides_key assigned,
    // then assign that existing one

    console.log("system body", systemBody);

    // setIsLoading(true);

    if (!existingSystem) {
      // @ts-ignore
      const { error: createSystemError } = await createSystem(systemBody);

      if (createSystemError) {
        // toast({
        //   status: "error",
        //   description: "Creating system failed.",
        // });
        console.log("error");
      } else {
        // toast.closeAll();
        handleChangeStep(5);
      }
    } else {
      // @ts-ignore
      const { error: updateSystemError } = await updateSystem(systemBody);

      // if (updateSystemError) {
      //   toast({
      //     status: "error",
      //     description: "Updating system failed.",
      //   });
      // } else {
      //   toast.closeAll();
      //   handleChangeStep(5);
      // }
    }

    // setIsLoading(false);
  };

  return (
    <Formik initialValues={initialValues} onSubmit={handleSubmitTest}>
      <Form>
        <Stack ml="100px" spacing={10}>
          <HorizontalStepper activeStep={1} steps={HORIZONTALSTEPS} />
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
                <FormLabel>System name</FormLabel>
                <Input
                  type="text"
                  id="name"
                  name="name"
                  focusBorderColor="gray.700"
                  onChange={handleChange}
                  onBlur={handleBlur}
                  placeholder={existingSystem?.name}
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

              {values.name ? (
                <Stack direction="row" mb={5} justifyContent="flex-end">
                  <FormLabel>System key</FormLabel>
                  <Input
                    type="text"
                    id="key"
                    name="key"
                    focusBorderColor="gray.700"
                    onChange={handleChange}
                    onBlur={handleBlur}
                    // placeholder={existingSystem?.system_key}
                    // TODO: is key stored? not seeing it in system info
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
              ) : null}

              {values.key ? (
                <Stack direction="row" mb={5} justifyContent="flex-end">
                  <FormLabel>Description</FormLabel>
                  <Input
                    type="text"
                    id="description"
                    name="description"
                    focusBorderColor="gray.700"
                    onChange={handleChange}
                    onBlur={handleBlur}
                    placeholder={existingSystem?.description}
                    value={values.description}
                    isInvalid={
                      touched.description && Boolean(errors.description)
                    }
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
              ) : null}

              {values.description ? (
                <Stack direction="row" mb={5} justifyContent="flex-end">
                  <FormLabel>System type</FormLabel>
                  <CreatableSelect
                    isClearable
                    id="type"
                    name="type"
                    placeholder={existingSystem?.system_type}
                    chakraStyles={chakraStyles}
                    size="md"
                  />
                  <Tooltip
                    fontSize="md"
                    label="Select a system type from the pre-approved list of system types."
                    placement="right"
                  >
                    <QuestionIcon boxSize={5} color="gray.400" />
                  </Tooltip>
                </Stack>
              ) : null}

              {/* values.types is nothing */}
              {/* {values.type ? ( */}
              <Stack direction="row" mb={5} justifyContent="flex-end">
                {/* <FormLabel>System tags</FormLabel> */}
                <CustomCreatableMultiSelect
                  name="tags"
                  label="System Tags"
                  options={[]}
                  /* <CreatableSelect
                isMulti
                isClearable
                id="tags"
                name="tags"
                noOptionsMessage={() => null}
                // options={[]}
                placeholder={existingSystem?.system_dependencies}
                // TODO: grab any existing system tags -- might need to destructure tags here
                // for the placeholder
                components={{
                  Menu: () => null,
                  DropdownIndicator: () => null,
                }}
                chakraStyles={chakraStyles}
                size="md"
              /> */
                />
                <Tooltip
                  fontSize="md"
                  label="Provide one or more tags to group the system. Tags are important as they allow you to filter and group systems for reporting and later review. Tags provide tremendous value as you scale - imagine you have thousands of systems, you’re going to thank us later for tagging!"
                  placement="right"
                >
                  <QuestionIcon boxSize={5} color="gray.400" />
                </Tooltip>
              </Stack>
              {/* ) : null} */}
            </FormControl>
          </Stack>
          <Box>
            <Button
              onClick={() => handleCancelSetup()}
              mr={2}
              size="sm"
              variant="outline"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              colorScheme="primary"
              size="sm"
              disabled={
                !values.name || !values.description || !values.key
                // !values.type ||
                // !values.tags
              }
              isLoading={isLoading}
            >
              Confirm and Continue
            </Button>
          </Box>
        </Stack>
      </Form>
    </Formik>
  );
};
export default DescribeSystemsForm;
