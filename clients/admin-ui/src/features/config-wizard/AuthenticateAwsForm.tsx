import {
  Accordion,
  AccordionButton,
  AccordionItem,
  AccordionPanel,
  Button,
  CloseButton,
  Heading,
  HStack,
  Spinner,
  Stack,
  Text,
  useDisclosure,
} from "@fidesui/react";
import { Form, Formik } from "formik";
import { useState } from "react";
import * as Yup from "yup";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { CustomSelect, CustomTextInput } from "~/features/common/form/inputs";
import {
  isErrorResult,
  ParsedError,
  parseError,
} from "~/features/common/helpers";
import {
  Dataset,
  GenerateResponse,
  GenerateTypes,
  System,
  ValidTargets,
} from "~/types/api";
import { RTKErrorResult } from "~/types/errors";

import DocsLink from "../common/DocsLink";
import WarningModal from "../common/WarningModal";
import {
  changeStep,
  selectOrganizationFidesKey,
  setSystemsForReview,
} from "./config-wizard.slice";
import {
  AWS_REGION_OPTIONS,
  DOCS_URL_AWS_PERMISSIONS,
  DOCS_URL_IAM_POLICY,
} from "./constants";
import { useGenerateMutation } from "./scanner.slice";
import ScannerError from "./ScannerError";

const isSystem = (sd: System | Dataset): sd is System => "system_type" in sd;

const initialValues = {
  aws_access_key_id: "",
  aws_secret_access_key: "",
  region_name: "",
};

type FormValues = typeof initialValues;

const ValidationSchema = Yup.object().shape({
  aws_access_key_id: Yup.string()
    .required()
    .trim()
    .matches(/^\w+$/, "Cannot contain spaces or special characters")
    .label("Access Key ID"),
  aws_secret_access_key: Yup.string()
    .required()
    .trim()
    .matches(/^[^\s]+$/, "Cannot contain spaces")
    .label("Secret"),
  region_name: Yup.string().required().label("Default Region"),
});

const AuthenticateAwsForm = () => {
  const organizationKey = useAppSelector(selectOrganizationFidesKey);
  const dispatch = useAppDispatch();
  const { isOpen, onOpen, onClose } = useDisclosure();

  const [scannerError, setScannerError] = useState<ParsedError>();

  const handleResults = (results: GenerateResponse["generate_results"]) => {
    const systems: System[] = (results ?? []).filter(isSystem);
    dispatch(setSystemsForReview(systems));
    dispatch(changeStep());
  };
  const handleError = (error: RTKErrorResult["error"]) => {
    const parsedError = parseError(error, {
      status: 500,
      message: "Our system encountered a problem while connecting to AWS.",
    });
    setScannerError(parsedError);
  };
  const handleCancel = () => {
    onClose();
    dispatch(changeStep(2));
  };

  const [generate, { isLoading }] = useGenerateMutation();

  const handleSubmit = async (values: FormValues) => {
    setScannerError(undefined);

    const result = await generate({
      organization_key: organizationKey,
      generate: {
        config: values,
        target: ValidTargets.AWS,
        type: GenerateTypes.SYSTEMS,
      },
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      handleResults(result.data.generate_results);
    }
  };

  const warningModalMessage = (
    <>
      <Text color="gray.500" mb={3}>
        Warning, you are about to cancel the scan!
      </Text>
      <Text color="gray.500" mb={3}>
        If you cancel scanning, the scanner will stop and no systems will be
        returned.
      </Text>
      <Text color="gray.500" mb={3}>
        Are you sure you want to cancel?
      </Text>
    </>
  );

  return (
    <>
      <Formik
        initialValues={initialValues}
        validationSchema={ValidationSchema}
        onSubmit={handleSubmit}
      >
        {({ isValid, isSubmitting, dirty }) => (
          <Form data-testid="authenticate-aws-form">
            <Stack spacing={10}>
              {isSubmitting ? (
                <Text
                  alignItems="center"
                  as="b"
                  color="gray.900"
                  display="flex"
                  fontSize="xl"
                >
                  System scanning in progress{" "}
                  <CloseButton
                    data-testid="close-scan-in-progress"
                    display="inline-block"
                    onClick={onOpen}
                  />
                </Text>
              ) : null}
              {isSubmitting ? (
                <Stack alignItems="center">
                  <Spinner
                    thickness="4px"
                    speed="0.65s"
                    emptyColor="gray.200"
                    color="gray.500"
                    size="md"
                  />
                </Stack>
              ) : null}
              {scannerError ? <ScannerError error={scannerError} /> : null}
              {!isSubmitting && !scannerError ? (
                <>
                  <Heading size="lg">Add a system</Heading>
                  <Accordion allowToggle border="transparent">
                    <AccordionItem>
                      {({ isExpanded }) => (
                        <>
                          <h2>
                            The scanner can be connected to your cloud
                            infrastructure provider to automatically scan and
                            create a list of all systems that may contain
                            personal data.
                            <AccordionButton
                              display="inline"
                              padding="0px"
                              ml="5px"
                              width="auto"
                              color="complimentary.500"
                            >
                              {isExpanded ? `(show less)` : `(show more)`}
                            </AccordionButton>
                          </h2>
                          <AccordionPanel padding="0px" mt="20px">
                            In order to run the scanner, please provide
                            credentials for authenticating to AWS. Please note,
                            the credentials must have the{" "}
                            <DocsLink href={DOCS_URL_AWS_PERMISSIONS}>
                              minimum permissions listed in the support
                              documentation here
                            </DocsLink>
                            . You can{" "}
                            <DocsLink href={DOCS_URL_IAM_POLICY}>
                              copy the sample IAM policy here
                            </DocsLink>
                            .
                          </AccordionPanel>
                        </>
                      )}
                    </AccordionItem>
                  </Accordion>

                  <Stack>
                    <CustomTextInput
                      name="aws_access_key_id"
                      label="Access Key ID"
                      // TODO(#724): These fields should link to the AWS docs, but that requires HTML
                      // content instead of just a string label. The message would be:
                      // "You can find more information about creating access keys and secrets on AWS docs here."
                      tooltip="AWS Access Key ID is the AWS ID associated with the account you want to use for scanning."
                    />
                    <CustomTextInput
                      type="password"
                      name="aws_secret_access_key"
                      label="Secret"
                      // "You can find more about creating access keys and secrets on AWS docs here."
                      tooltip="The secret access key is generated when you create your new access key ID."
                    />
                    <CustomSelect
                      name="region_name"
                      label="Default Region"
                      // "You can learn more about regions in AWS docs here."
                      tooltip="Specify the default region in which your infrastructure is located. This is necessary for successful scanning."
                      options={AWS_REGION_OPTIONS}
                    />
                  </Stack>
                </>
              ) : null}
              <HStack>
                <Button
                  variant="outline"
                  onClick={!isSubmitting ? handleCancel : onOpen}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  isDisabled={!dirty || !isValid}
                  isLoading={isLoading}
                  data-testid="submit-btn"
                >
                  Save and Continue
                </Button>
              </HStack>
            </Stack>
          </Form>
        )}
      </Formik>
      <WarningModal
        isOpen={isOpen}
        onClose={onClose}
        handleConfirm={handleCancel}
        title="Cancel Scan!"
        message={warningModalMessage}
        confirmButtonText="Yes, Cancel"
        cancelButtonText="No, Continue Scanning"
      />
    </>
  );
};

export default AuthenticateAwsForm;
