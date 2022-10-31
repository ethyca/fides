/* eslint-disable @typescript-eslint/no-unused-vars */
import {
  Box,
  Button,
  ButtonGroup,
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerFooter,
  DrawerHeader,
  DrawerOverlay,
  FormControl,
  FormErrorMessage,
  FormLabel,
  HStack,
  Input,
  MenuItem,
  NumberDecrementStepper,
  NumberIncrementStepper,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  Switch,
  Text,
  useDisclosure,
  VStack,
} from "@fidesui/react";
import {
  Field,
  FieldInputProps,
  FieldMetaProps,
  Form,
  Formik,
  FormikProps,
} from "formik";
import { ChangeEvent, useRef } from "react";
import * as Yup from "yup";

const initialValues = {
  email: "",
  notify: false,
  minErrorCount: 0,
};

type FormValues = typeof initialValues;

const validationSchema = Yup.object().shape({
  email: Yup.string()
    .email("Must be a valid email format")
    .required("Email is required"),
});

const ConfigureAlerts: React.FC = () => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const firstField = useRef(null);

  const handleSubmit = async (values: FormValues, _actions: any) => {
    console.log(values);
    onClose();
  };

  return (
    <>
      <MenuItem
        onClick={onOpen}
        _focus={{ bg: "gray.100", color: "complimentary.500" }}
      >
        Configure alerts
      </MenuItem>
      <Formik
        enableReinitialize
        initialValues={initialValues}
        onSubmit={handleSubmit}
        validateOnBlur={false}
        validateOnChange={false}
        validationSchema={validationSchema}
      >
        {(props: FormikProps<FormValues>) => (
          <Drawer
            isOpen={isOpen}
            placement="right"
            initialFocusRef={firstField}
            onClose={onClose}
            size="lg"
          >
            <DrawerOverlay />
            <DrawerContent color="gray.900">
              <DrawerCloseButton />
              <DrawerHeader color="gray.900">
                <Text fontSize="2xl" fontWeight="normal" mb={4}>
                  Configure alerts and notifications
                </Text>
                <Box mt="26px">
                  <Text fontSize="md" fontWeight="normal">
                    Setup your alerts to send you a notification when there are
                    any processing failures. You can also setup a threshold for
                    connector failures for Fides to notify you after X amount of
                    failures have occurred.
                  </Text>
                </Box>
              </DrawerHeader>
              <DrawerBody mt="20px">
                <Form id="configure-alerts-form" noValidate>
                  <Text fontSize="md">Contact details</Text>
                  <VStack align="stretch" gap="29px" mt="14px">
                    <HStack>
                      <Field id="email" name="email">
                        {({
                          field,
                          meta,
                        }: {
                          field: FieldInputProps<string>;
                          meta: FieldMetaProps<string>;
                        }) => (
                          <FormControl
                            alignItems="baseline"
                            display="inline-flex"
                            isRequired
                            isInvalid={!!(meta.error && meta.touched)}
                          >
                            <FormLabel fontSize="md" htmlFor="email" w="30%">
                              Email
                            </FormLabel>
                            <VStack align="flex-start" w="inherit">
                              <Input
                                {...field}
                                autoComplete="off"
                                placeholder="Please enter email"
                                ref={firstField}
                                size="sm"
                              />
                              <FormErrorMessage>
                                {props.errors.email}
                              </FormErrorMessage>
                            </VStack>
                          </FormControl>
                        )}
                      </Field>
                    </HStack>
                    <HStack>
                      <Field id="notify" name="notify">
                        {({ field }: { field: FieldInputProps<string> }) => (
                          <FormControl
                            alignItems="center"
                            display="flex"
                            mt="45px"
                          >
                            <FormLabel fontSize="md" mb="0">
                              Notify me immediately if there are any DSR
                              processing errors
                            </FormLabel>
                            <Switch
                              {...field}
                              colorScheme="secondary"
                              isChecked={field.checked}
                              onChange={(
                                event: ChangeEvent<HTMLInputElement>
                              ) => {
                                field.onChange(event);
                                props.setFieldValue("minErrorCount", 0);
                              }}
                            />
                          </FormControl>
                        )}
                      </Field>
                    </HStack>
                  </VStack>
                  <Text color="#757575" fontSize="sm" mt="11px">
                    If selected, then Fides will notify you by your chosen
                    method of communication every time the system encounters a
                    data subject request processing error. You can turn this off
                    anytime and setup a more suitable notification method below
                    if you wish.
                  </Text>
                  {props.values.notify && (
                    <HStack mt="34px">
                      <Field id="minErrorCount" name="minErrorCount">
                        {({ field }: { field: FieldInputProps<string> }) => (
                          <FormControl alignItems="center" display="flex">
                            <Text>Notify me after</Text>
                            <NumberInput
                              allowMouseWheel
                              color="gray.700"
                              defaultValue={0}
                              min={0}
                              ml="8px"
                              mr="8px"
                              onChange={(_valueAsString, valueAsNumber) => {
                                props.setFieldValue(
                                  "minErrorCount",
                                  valueAsNumber
                                );
                              }}
                              size="sm"
                              w="80px"
                            >
                              <NumberInputField {...field} />
                              <NumberInputStepper>
                                <NumberIncrementStepper />
                                <NumberDecrementStepper />
                              </NumberInputStepper>
                            </NumberInput>
                            <Text>DSR processing errors </Text>
                          </FormControl>
                        )}
                      </Field>
                    </HStack>
                  )}
                </Form>
              </DrawerBody>
              <DrawerFooter justifyContent="flex-start">
                <ButtonGroup size="sm" spacing="8px" variant="outline">
                  <Button onClick={onClose} variant="outline">
                    Cancel
                  </Button>
                  <Button
                    bg="primary.800"
                    color="white"
                    form="configure-alerts-form"
                    isLoading={props.isSubmitting}
                    loadingText="Submitting"
                    size="sm"
                    variant="solid"
                    type="submit"
                    _active={{ bg: "primary.500" }}
                    _hover={{ bg: "primary.400" }}
                  >
                    Save
                  </Button>
                </ButtonGroup>
              </DrawerFooter>
            </DrawerContent>
          </Drawer>
        )}
      </Formik>
    </>
  );
};

export default ConfigureAlerts;
