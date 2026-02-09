/* eslint-disable @typescript-eslint/no-unused-vars */
import {
  Button,
  ChakraBox as Box,
  ChakraCheckbox as Checkbox,
  ChakraDivider as Divider,
  ChakraDrawer as Drawer,
  ChakraDrawerBody as DrawerBody,
  ChakraDrawerCloseButton as DrawerCloseButton,
  ChakraDrawerContent as DrawerContent,
  ChakraDrawerFooter as DrawerFooter,
  ChakraDrawerHeader as DrawerHeader,
  ChakraDrawerOverlay as DrawerOverlay,
  ChakraFormControl as FormControl,
  ChakraFormLabel as FormLabel,
  ChakraHStack as HStack,
  ChakraText as Text,
  ChakraVStack as VStack,
  useChakraDisclosure as useDisclosure,
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
        <Button onClick={onOpen} size="small">
          Review
        </Button>
      )}
      {!data?.checked && (
        <Button onClick={onOpen} size="small" type="primary">
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
        {(_props) => (
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
                <div className="flex gap-2">
                  <Button onClick={onClose}>Cancel</Button>
                  <Button
                    form="manual-detail-form"
                    loading={isSubmitting}
                    htmlType="submit"
                  >
                    Save
                  </Button>
                </div>
              </DrawerFooter>
            </DrawerContent>
          </Drawer>
        )}
      </Formik>
    </>
  );
};

export default ManualErasureProcessingDetail;
