import {
  Box,
  Button,
  Stack,
  useToast,
  Text,
  ButtonGroup,
  Heading,
} from "@fidesui/react";
import React, { useEffect, useState } from "react";

import { CustomTextInput } from "common/form/inputs";
import { useAppDispatch } from "~/app/hooks";
import {
  isErrorResult,
  ParsedError,
  parseError,
} from "~/features/common/helpers";
import { successToastParams } from "~/features/common/toast";
import { useGetWebScanQuery, WebsiteScan } from "~/features/plus/plus.slice";
import { isAPIError, RTKErrorResult } from "~/types/errors";

import { changeStep, setSystemsForReview } from "./config-wizard.slice";
import ScannerError from "./ScannerError";
import ScannerLoading from "./ScannerLoading";
import { Form, Formik, FormikHelpers } from "formik";
import * as Yup from "yup";

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
  // const [webScanQuery, results] = useGetWebScanQuery();
  // webScanQuery()

  const skip = true;
  const { isSuccess, isLoading, isError, error, data } = useGetWebScanQuery(
    initialValues,
    {
      skip,
    }
  );

  const [scannerError, setScannerError] = useState<ParsedError>();

  const handleError = (requestError: RTKErrorResult["error"]) => {
    const parsedError = parseError(requestError, {
      status: 500,
      message: "Our system encountered a problem while scanning your website.",
    });
    setScannerError(parsedError);
  };

  const handleCancel = () => {
    dispatch(changeStep(2));
  };

  useEffect(() => {
    if (isError) {
      handleError(error as RTKErrorResult["error"]);
    }
  }, [isError, error, handleError]);

  /**
  //  * When the scan is finished, handle the resultV
  //  * in order not to trigger the initial scan again.
  //  */
  useEffect(() => {
    const handleResults = async () => {
      if (data) {
        const toastMsg = `Your scan was successfully completed, with ##### systems detected!`;
        // const toastMsg = `Your scan was successfully completed, with ${data.added_egress.l} systems detected!`
        toast(successToastParams(toastMsg));
        dispatch(changeStep());
      }
    };
    if (isSuccess) {
      handleResults();
    }
  }, [data, toast, dispatch, isSuccess]);

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
        onSubmit={() => {}}
        validationSchema={validationSchema}
      >
        {({ isSubmitting, dirty, isValid }) => (
          <Box maxWidth="800px">
            {!isSubmitting ? (
              <Form>
                <Heading as="h3" size="lg" fontWeight="semibold" mb={10}>
                  Website Scan
                </Heading>
                <Text mb={7}>
                  Provide a target website(e.g. "https://ethyca.com"), and Fides
                  will automatically scanand generate a list of systems based on
                  the web requests detected in the browser.
                </Text>
                <Box mb={5}>
                  <CustomTextInput label="Website Url" name="url" />
                </Box>
                <Box mb={5}>
                  <CustomTextInput label="Website Name" name="name" />
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
