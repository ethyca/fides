/* eslint-disable @typescript-eslint/no-unused-vars */
import {
  Box,
  Button,
  ButtonGroup,
  Checkbox,
  Divider,
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
  Text,
  useDisclosure,
  VStack,
} from "fidesui";
import { Field, FieldInputProps, Form, Formik } from "formik";
import { PatchUploadManualWebhookDataRequest } from "privacy-requests/types";
import React, { useRef } from "react";
import * as Yup from "yup";

import { ManualProcessingDetailProps } from "./types";

const ManualErasureProcessingDetail = ({
  connectorName,
  data,
  isSubmitting = false,
  onSaveClick,
}: ManualProcessingDetailProps) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const firstField = useRef(null);

  const handleSubmit = async (values: any, _actions: any) => {
    const params: PatchUploadManualWebhookDataRequest = {
      connection_key: data.connection_key,
      privacy_request_id: data.privacy_request_id,
      body: { ...values } as object,
    };
    onSaveClick(params);
    onClose();
  };

  return (
    <>
      {data?.checked && (
        <Button
          color="gray.700"
          fontSize="xs"
          h="24px"
          onClick={onOpen}
          variant="outline"
          w="58px"
        >
          Review
        </Button>
      )}
      {!data?.checked && (
        <Button
          color="white"
          bg="primary.800"
          fontSize="xs"
          h="24px"
          onClick={onOpen}
          w="127px"
          _hover={{ bg: "primary.400" }}
          _active={{ bg: "primary.500" }}
        >
          Begin manual input
        </Button>
      )}
      <Formik
        enableReinitialize
        initialValues={{ ...data.fields }}
        onSubmit={handleSubmit}
        validateOnBlur={false}
        validateOnChange={false}
        validationSchema={Yup.object().shape({})}
      >
        {/* @ts-ignore */}
        {(_props: FormikProps<Values>) => (
          <Drawer
            isOpen={isOpen}
            placement="right"
            initialFocusRef={firstField}
            onClose={onClose}
            size="lg"
          >
            <DrawerOverlay />
            <DrawerContent>
              <DrawerCloseButton />
              <DrawerHeader color="gray.900">
                <Text fontSize="xl" mb={8}>
                  {connectorName}
                </Text>
                <Divider />
                <Text fontSize="md" mt="4">
                  Manual erasure
                </Text>
                <Box mt="8px">
                  <Text color="gray.700" fontSize="sm" fontWeight="normal">
                    Please delete the following PII fields associated with the
                    selected subject if they are available. Once deleted, check
                    the box to confirm the deletion.
                  </Text>
                </Box>
              </DrawerHeader>
              <DrawerBody>
                <Form id="manual-detail-form" noValidate>
                  <VStack align="stretch" gap="16px">
                    {Object.entries(data.fields).map(([key]) => (
                      <HStack key={key}>
                        <Field id={key} name={key}>
                          {({ field }: { field: FieldInputProps<string> }) => (
                            <FormControl
                              alignItems="baseline"
                              display="inline-flex"
                            >
                              <FormLabel
                                color="gray.900"
                                fontSize="14px"
                                fontWeight="semibold"
                                htmlFor={key}
                                w="50%"
                              >
                                {key}
                              </FormLabel>
                              <Checkbox
                                {...field}
                                isChecked={!!field.value}
                                onChange={field.onChange}
                                name={key}
                                id={key}
                              />
                            </FormControl>
                          )}
                        </Field>
                      </HStack>
                    ))}
                  </VStack>
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
                    form="manual-detail-form"
                    isLoading={isSubmitting}
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

export default ManualErasureProcessingDetail;
