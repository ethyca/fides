import {
  Accordion,
  AccordionButton,
  AccordionItem,
  AccordionPanel,
  Button,
  Divider,
  Heading,
  HStack,
  Stack,
  Text,
} from "@fidesui/react";
import { Form, Formik } from "formik";
import { useState } from "react";
import * as Yup from "yup";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import DocsLink from "~/features/common/DocsLink";
import { CustomTextInput } from "~/features/common/form/inputs";
import {
  isErrorResult,
  ParsedError,
  parseError,
} from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import {
  Dataset,
  GenerateResponse,
  GenerateTypes,
  System,
  ValidTargets,
} from "~/types/api";
import { RTKErrorResult } from "~/types/errors";

import {
  changeStep,
  selectOrganizationFidesKey,
  setSystemsForReview,
} from "./config-wizard.slice";
//   import {
//     OKTA_REGION_OPTIONS,
//     DOCS_URL_OKTA_PERMISSIONS,
//     DOCS_URL_IAM_POLICY,
//   } from "./constants";
import { useGenerateMutation } from "./scanner.slice";
import ScannerError from "./ScannerError";
import ScannerLoading from "./ScannerLoading";

const isSystem = (sd: System | Dataset): sd is System => "system_type" in sd;

const initialValues = {
  orgUrl: "",
  token: "",
};

type FormValues = typeof initialValues;

const ValidationSchema = Yup.object().shape({
  orgUrl: Yup.string()
    .required()
    .trim()
    .matches(/^[^\s]+$/, "Cannot contain spaces")
    .label("URL"),
  token: Yup.string()
    .required()
    .trim()
    .matches(/^[^\s]+$/, "Cannot contain spaces")
    .label("Token"),
});

const AuthenticateOktaForm = () => {
  const organizationKey = useAppSelector(selectOrganizationFidesKey);
  const dispatch = useAppDispatch();
  const { successAlert } = useAlert();

  const [scannerError, setScannerError] = useState<ParsedError>();

  const handleResults = (results: GenerateResponse["generate_results"]) => {
    const systems: System[] = (results ?? []).filter(isSystem);
    dispatch(setSystemsForReview(systems));
    dispatch(changeStep());
    successAlert(
      `Your scan was successfully completed, with ${systems.length} new systems detected!`,
      `Scan Successfully Completed`,
      { isClosable: true }
    );
  };
  const handleError = (error: RTKErrorResult["error"]) => {
    const parsedError = parseError(error, {
      status: 500,
      message: "Our system encountered a problem while connecting to Okta.",
    });
    setScannerError(parsedError);
  };
  const handleCancel = () => {
    dispatch(changeStep(2));
  };

  const [generate, { isLoading }] = useGenerateMutation();

  const handleSubmit = async (values: FormValues) => {
    setScannerError(undefined);

    const result = await generate({
      organization_key: organizationKey,
      generate: {
        config: values,
        target: ValidTargets.OKTA,
        type: GenerateTypes.SYSTEMS,
      },
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      handleResults(result.data.generate_results);
    }
  };

  return (
    <Formik
      initialValues={initialValues}
      validationSchema={ValidationSchema}
      onSubmit={handleSubmit}
    >
      {({ isValid, isSubmitting, dirty }) => (
        <Form data-testid="authenticate-okta-form">
          <Stack spacing={10}>
            {isSubmitting ? (
              <ScannerLoading
                title="System scanning in progress"
                onClose={handleCancel}
              />
            ) : null}

            {scannerError ? <ScannerError error={scannerError} /> : null}
            {!isSubmitting && !scannerError ? (
              <>
                <Heading size="lg">Authenticate Scanner</Heading>
                <Accordion allowToggle border="transparent">
                  <AccordionItem>
                    {({ isExpanded }) => (
                      <>
                        <h2>
                          The scanner can be connected to your sign-on provider
                          to automatically scan and create a list of all systems
                          that your team are using that may contain personal
                          data.
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
                          Currently the scanner supports certain Okta. We will
                          be adding support for other sign-on providers (e.g.
                          Auth0,Microsoft, Google) shortly, please let us know
                          if you have specific requests.
                        </AccordionPanel>
                      </>
                    )}
                  </AccordionItem>
                </Accordion>
                <Divider m="20px 0px !important" />
                <Text m="0px !important">
                  In order to run the scanner, please provide your Okta token.
                  You can find{" "}
                  <DocsLink href="https://help.okta.com/oie/en-us/Content/Topics/Security/API.htm">
                    instructions here{" "}
                  </DocsLink>{" "}
                  on how to retrieve a suitable token from your Okta
                  administration
                </Text>
                panel.
                <Stack>
                  <CustomTextInput
                    name="okta_org_url"
                    label="Org URL:"
                    tooltip="Need text"
                  />
                  <CustomTextInput
                    name="okta_token"
                    label="Okta token:"
                    tooltip="Need text"
                  />
                </Stack>
              </>
            ) : null}
            {!isSubmitting ? (
              <HStack>
                <Button variant="outline" onClick={handleCancel}>
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
            ) : null}
          </Stack>
        </Form>
      )}
    </Formik>
  );
};

export default AuthenticateOktaForm;
