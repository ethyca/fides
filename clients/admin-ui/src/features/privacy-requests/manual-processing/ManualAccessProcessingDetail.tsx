/* eslint-disable @typescript-eslint/no-unused-vars */
import {
  Button,
  ChakraBox as Box,
  ChakraDivider as Divider,
  ChakraFormControl as FormControl,
  ChakraFormLabel as FormLabel,
  ChakraHStack as HStack,
  ChakraInput as Input,
  ChakraText as Text,
  ChakraVStack as VStack,
  Drawer,
  Flex,
} from "fidesui";
import { Field, FieldInputProps, Form, Formik } from "formik";
import { PatchUploadManualWebhookDataRequest } from "privacy-requests/types";
import React, { useState } from "react";
import * as Yup from "yup";

import { ManualProcessingDetailProps } from "./types";

const ManualAccessProcessingDetail = ({
  connectorName,
  data,
  isSubmitting = false,
  onSaveClick,
}: ManualProcessingDetailProps) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleSubmit = async (values: any, _actions: any) => {
    const params: PatchUploadManualWebhookDataRequest = {
      connection_key: data.connection_key,
      privacy_request_id: data.privacy_request_id,
      body: { ...values } as object,
    };
    onSaveClick(params);
    setIsOpen(false);
  };

  return (
    <>
      {data?.checked && (
        <Button onClick={() => setIsOpen(true)} size="small">
          Review
        </Button>
      )}
      {!data?.checked && (
        <Button onClick={() => setIsOpen(true)} size="small" type="primary">
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
            open={isOpen}
            onClose={() => setIsOpen(false)}
            size="large"
            title={
              <>
                <Text fontSize="xl" mb={8}>
                  {connectorName}
                </Text>
                <Divider />
                <Text fontSize="md" mt="4">
                  Manual access
                </Text>
                <Box mt="8px">
                  <Text color="gray.700" fontSize="sm" fontWeight="normal">
                    Please complete the following PII fields that have been
                    collected for the selected subject.
                  </Text>
                </Box>
              </>
            }
            footer={
              <Flex gap="small">
                <Button onClick={() => setIsOpen(false)}>Cancel</Button>
                <Button
                  form="manual-detail-form"
                  loading={isSubmitting}
                  htmlType="submit"
                >
                  Save
                </Button>
              </Flex>
            }
          >
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
                          <Input
                            {...field}
                            autoComplete="off"
                            color="gray.700"
                            placeholder={`Please enter ${key}`}
                            size="sm"
                          />
                        </FormControl>
                      )}
                    </Field>
                  </HStack>
                ))}
              </VStack>
            </Form>
          </Drawer>
        )}
      </Formik>
    </>
  );
};

export default ManualAccessProcessingDetail;
