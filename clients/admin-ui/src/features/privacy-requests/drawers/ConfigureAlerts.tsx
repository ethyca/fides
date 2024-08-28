/* eslint-disable @typescript-eslint/no-unused-vars */
import {
  BellIcon,
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
  FormLabel,
  HStack,
  IconButton,
  NumberDecrementStepper,
  NumberIncrementStepper,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  Switch,
  Text,
  useDisclosure,
  VStack,
} from "fidesui";
import {
  Field,
  FieldArray,
  FieldInputProps,
  FieldMetaProps,
  Form,
  Formik,
  FormikHelpers,
  FormikProps,
} from "formik";
import { ChangeEvent, useEffect, useRef, useState } from "react";
import * as Yup from "yup";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";

import EmailChipList from "../EmailChipList";
import {
  useGetNotificationQuery,
  useSaveNotificationMutation,
} from "../privacy-requests.slice";

const DEFAULT_MIN_ERROR_COUNT = 1;

const validationSchema = Yup.object().shape({
  emails: Yup.array(Yup.string()).when(["notify"], {
    is: true,
    then: () =>
      Yup.array(Yup.string())
        .min(1, "Must enter at least one valid email")
        .label("Email"),
  }),
  notify: Yup.boolean(),
  minErrorCount: Yup.number().required(),
});

const ConfigureAlerts = () => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [formValues, setFormValues] = useState({
    emails: [] as string[],
    notify: false,
    minErrorCount: DEFAULT_MIN_ERROR_COUNT,
  });
  const firstField = useRef(null);
  const { errorAlert, successAlert } = useAlert();
  const [skip, setSkip] = useState(true);

  const { data } = useGetNotificationQuery(undefined, { skip });
  const [saveNotification] = useSaveNotificationMutation();

  const handleSubmit = async (
    values: typeof formValues,
    helpers: FormikHelpers<typeof formValues>,
  ) => {
    helpers.setSubmitting(true);
    const payload = await saveNotification({
      email_addresses: values.emails,
      notify_after_failures: values.notify ? values.minErrorCount : 0,
    });
    if ("error" in payload) {
      errorAlert(
        getErrorMessage(payload.error),
        `Configure alerts and notifications has failed to save due to the following:`,
      );
    } else {
      successAlert(`Configure alerts and notifications saved successfully.`);
    }
    helpers.setSubmitting(false);
    onClose();
  };

  useEffect(() => {
    if (isOpen) {
      setSkip(false);
    }
    if (data) {
      setFormValues({
        emails: data.email_addresses,
        notify: data.notify_after_failures !== 0,
        minErrorCount: data.notify_after_failures,
      });
    }
  }, [data, isOpen]);

  return (
    <>
      <IconButton
        onClick={onOpen}
        variant="outline"
        size="xs"
        title="Configure alerts"
        aria-label="Configure alerts"
        icon={<BellIcon />}
      />
      <Formik
        enableReinitialize
        initialValues={formValues}
        onSubmit={handleSubmit}
        validationSchema={validationSchema}
      >
        {(props: FormikProps<typeof formValues>) => (
          <Drawer
            isOpen={isOpen}
            placement="right"
            initialFocusRef={firstField}
            onClose={() => {
              props.resetForm();
              onClose();
            }}
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
                      <FieldArray
                        name="emails"
                        render={(fieldArrayProps) => (
                          <EmailChipList
                            {...fieldArrayProps}
                            isRequired={props.values.notify}
                            ref={firstField}
                          />
                        )}
                      />
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
                              isChecked={props.values.notify}
                              onChange={(
                                event: ChangeEvent<HTMLInputElement>,
                              ) => {
                                field.onChange(event);
                                props.setFieldValue(
                                  "minErrorCount",
                                  DEFAULT_MIN_ERROR_COUNT,
                                );
                                if (!event.target.checked) {
                                  setTimeout(() => {
                                    props.setFieldTouched("emails", false);
                                  }, 0);
                                }
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
                        {({
                          field,
                          meta,
                        }: {
                          field: FieldInputProps<string>;
                          meta: FieldMetaProps<string>;
                        }) => (
                          <FormControl
                            alignItems="center"
                            display="flex"
                            isInvalid={!!(meta.error && meta.touched)}
                            isRequired
                          >
                            <Text>Notify me after</Text>
                            <NumberInput
                              allowMouseWheel
                              color="gray.700"
                              defaultValue={
                                props.values.minErrorCount ||
                                DEFAULT_MIN_ERROR_COUNT
                              }
                              min={DEFAULT_MIN_ERROR_COUNT}
                              ml="8px"
                              mr="8px"
                              onChange={(_valueAsString, valueAsNumber) => {
                                props.setFieldValue(
                                  "minErrorCount",
                                  valueAsNumber,
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
                  <Button
                    onClick={() => {
                      props.resetForm();
                      onClose();
                    }}
                    variant="outline"
                  >
                    Cancel
                  </Button>
                  <Button
                    bg="primary.800"
                    color="white"
                    form="configure-alerts-form"
                    isDisabled={props.isSubmitting}
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
