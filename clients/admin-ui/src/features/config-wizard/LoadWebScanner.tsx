import {
  Box,
  Button,
  ButtonGroup,
  Heading,
  Stack,
  Text,
  useToast,
} from "@fidesui/react";
import { CustomTextInput } from "common/form/inputs";
import { Form, Formik, FormikHelpers } from "formik";
import React, { useCallback, useEffect, useState } from "react";
import * as Yup from "yup";

import { useAppDispatch } from "~/app/hooks";
import { ParsedError, parseError } from "~/features/common/helpers";
import { successToastParams } from "~/features/common/toast";
import { useGetWebScanMutation, WebsiteScan } from "~/features/plus/plus.slice";
import { System } from "~/types/api";
import { RTKErrorResult } from "~/types/errors";

import { changeStep, setSystemsForReview } from "./config-wizard.slice";
import ScannerError from "./ScannerError";
import ScannerLoading from "./ScannerLoading";

const initialValues: WebsiteScan = {
  url: "",
  name: "",
};
type FormValues = typeof initialValues;
const validationSchema = Yup.object().shape({
  url: Yup.string().url().required().label("Website URL"),
  name: Yup.string().required().label("Website Name"),
});
/**
 * POC component
 */
const LoadWebScanner = () => {
  const dispatch = useAppDispatch();
  const toast = useToast();
  const [getWebScan, getWebScanResults] = useGetWebScanMutation();

  const [scannerError, setScannerError] = useState<ParsedError>();

  const handleError = useCallback((requestError: RTKErrorResult["error"]) => {
    const parsedError = parseError(requestError, {
      status: 500,
      message: "Our system encountered a problem while scanning your website.",
    });
    setScannerError(parsedError);
  }, []);

  const handleCancel = () => {
    dispatch(changeStep(2));
  };

  useEffect(() => {
    if (getWebScanResults.isError) {
      handleError(getWebScanResults.error as RTKErrorResult["error"]);
    }
  }, [getWebScanResults, handleError]);

  /**
  //  * When the scan is finished, handle the resultV
  //  * in order not to trigger the initial scan again.
  //  */
  useEffect(() => {
    const handleResults = async () => {
      if (getWebScanResults.data) {
        const toastMsg = `Your scan was successfully completed, with ${getWebScanResults.data.length} systems detected!`;
        toast(successToastParams(toastMsg));
        dispatch(changeStep());
      }
    };
    if (getWebScanResults.isSuccess) {
      handleResults();
    }
  }, [toast, dispatch, getWebScanResults]);

  const handleSubmit = useCallback(
    (values: FormValues, formikHelpers: FormikHelpers<FormValues>) => {
      const { setSubmitting } = formikHelpers;
      getWebScan(values).then((response) => {
        // @ts-ignore
        const systems = response.data as System[];
        dispatch(setSystemsForReview(systems));
        setSubmitting(false);
      });
    },
    [getWebScan, dispatch]
  );

  if (scannerError) {
    return (
      <Stack>
        <ScannerError error={scannerError} />
        <Box>
          <Button
            variant="outline"
            onClick={handleCancel}
            data-testid="cancel-btn"
          >
            Cancel
          </Button>
        </Box>
      </Stack>
    );
  }

  return (
    <Box
      id="web-scanner-form"
      display="flex"
      justifyContent="center"
      width="100%"
    >
      <Formik
        initialValues={initialValues}
        onSubmit={handleSubmit}
        validationSchema={validationSchema}
      >
        {({ isSubmitting, dirty, isValid }) => (
          <Box maxWidth="800px">
            {!isSubmitting ? (
              <Form>
                <Heading as="h3" size="lg" fontWeight="semibold" mb={10}>
                  Configure scanner
                </Heading>
                <Text mb={7}>
                  The scanner can be connected to your website to automatically
                  scan and create a list of all systems that may transmit
                  personal data to other systems.
                </Text>
                <Box mb={5}>
                  <CustomTextInput
                    label="Website Url"
                    name="url"
                    placeholder="https://www.ethyca.com"
                  />
                </Box>
                <Box mb={5}>
                  <CustomTextInput
                    label="Website Name"
                    name="name"
                    placeholder="Ethyca, inc"
                  />
                </Box>
                <ButtonGroup size="sm" spacing={3} width="300px">
                  <Button
                    width="100%"
                    maxWidth="115px"
                    variant="outline"
                    colorScheme="gray.200"
                    disabled={isSubmitting}
                    onClick={handleCancel}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    width="100%"
                    maxWidth="152px"
                    colorScheme="primary"
                    variant="solid"
                    disabled={!dirty || !isValid}
                    isLoading={isSubmitting}
                  >
                    Save and Continue
                  </Button>
                </ButtonGroup>
              </Form>
            ) : (
              <ScannerLoading
                title="Web scan in progress"
                onClose={handleCancel}
              />
            )}
          </Box>
        )}
      </Formik>
    </Box>
  );
};

export default LoadWebScanner;
