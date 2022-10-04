/* eslint-disable @typescript-eslint/no-unused-vars */
import {
  Box,
  Button,
  ButtonGroup,
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
  Input,
  Text,
  useDisclosure,
  VStack,
} from "@fidesui/react";
import { Field, Form, Formik } from "formik";
import { PatchUploadManualWebhookDataRequest } from "privacy-requests/types";
import React, { useRef } from "react";
import * as Yup from "yup";

import { ManualInputData } from "./types";

type ManualProcessingDetailProps = {
  connectorName: string;
  data: ManualInputData;
  isSubmitting: boolean;
  onSaveClick: (params: PatchUploadManualWebhookDataRequest) => void;
};

const ManualProcessingDetail: React.FC<ManualProcessingDetailProps> = ({
  connectorName,
  data,
  isSubmitting = false,
  onSaveClick,
}) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const firstField = useRef();

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
            // @ts-ignore
            initialFocusRef={firstField}
            onClose={onClose}
            size="lg"
          >
            <DrawerOverlay />
            <DrawerContent>
              <DrawerCloseButton />
              <DrawerHeader color="gray.900">
                <Text fontSize="xl" mb={4}>
                  {connectorName}
                </Text>
                <Divider />
                <Text fontSize="md" mt="8">
                  PII Requirements
                </Text>
                <Box mt="8px">
                  <Text color="gray.700" fontSize="sm" fontWeight="normal">
                    Please complete the following PII fields that have been
                    collected for the selected subject.
                  </Text>
                </Box>
              </DrawerHeader>
              <DrawerBody mt="24px">
                <Form id="manual-detail-form" noValidate>
                  <VStack align="stretch" gap="16px">
                    {Object.entries(data.fields).map(([key], index) => (
                      <HStack key={key}>
                        <Field id={key} name={key}>
                          {({ field }: { field: any }) => (
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
                              <Input
                                {...field}
                                autoComplete="off"
                                color="gray.700"
                                placeholder={`Please enter ${key}`}
                                ref={index === 0 ? firstField : undefined}
                                size="sm"
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

export default ManualProcessingDetail;
