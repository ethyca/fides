import { Box, Button, Divider, Stack } from "@fidesui/react";
import { useRouter } from "next/router";
import React from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { CloseSolidIcon } from "~/features/common/Icon";
import { System } from "~/types/api";

import HorizontalStepper from "../common/HorizontalStepper";
import Stepper from "../common/Stepper";
import AddSystemForm from "./AddSystemForm";
import AuthenticateScanner from "./AuthenticateScanner";
import {
  changeReviewStep,
  changeStep,
  selectReviewStep,
  selectStep,
  selectSystemFidesKey,
  setSystemFidesKey,
} from "./config-wizard.slice";
import { HORIZONTAL_STEPS, STEPS } from "./constants";
import DescribeSystemsForm from "./DescribeSystemsForm";
import OrganizationInfoForm from "./OrganizationInfoForm";
import PrivacyDeclarationForm from "./PrivacyDeclarationForm";
import ReviewSystemForm from "./ReviewSystemForm";
import ScanResultsForm from "./ScanResultsForm";
import SuccessPage from "./SuccessPage";
import ViewYourDataMapPage from "./ViewYourDataMapPage";

const ConfigWizardWalkthrough = () => {
  const router = useRouter();

  const step = useAppSelector(selectStep);
  const reviewStep = useAppSelector(selectReviewStep);
  const dispatch = useAppDispatch();
  const systemKey = useAppSelector(selectSystemFidesKey);

  const handleCancelSetup = () => {
    router.push("/");
  };

  const handleDescribeSuccess = (values: System) => {
    dispatch(setSystemFidesKey(values.fides_key ?? ""));
    dispatch(changeReviewStep());
  };

  const handleDeclareSuccess = () => {
    dispatch(changeReviewStep());
  };

  return (
    <>
      <Box bg="white">
        <Button
          bg="transparent"
          fontWeight="500"
          m={2}
          ml={6}
          onClick={handleCancelSetup}
        >
          <CloseSolidIcon /> Cancel setup
        </Button>
      </Box>
      <Divider orientation="horizontal" />
      <Stack direction={["column", "row"]}>
        <Stack bg="white" height="100vh" maxW="60%">
          <Stack mt={10} mb={10} direction="row" spacing="24px">
            <Box flexShrink={0}>
              <Stepper
                activeStep={step}
                setActiveStep={(s) => dispatch(changeStep(s))}
                steps={STEPS}
              />
            </Box>
            {step === 1 ? <OrganizationInfoForm /> : null}
            {step === 2 ? <AddSystemForm /> : null}
            {step === 3 ? <AuthenticateScanner /> : null}
            {step === 4 ? <ScanResultsForm /> : null}
            {step === 5 ? (
              <Stack direction="column">
                {reviewStep <= 3 ? (
                  <HorizontalStepper
                    activeStep={reviewStep}
                    steps={HORIZONTAL_STEPS}
                  />
                ) : null}
                {reviewStep === 1 && (
                  <DescribeSystemsForm
                    onCancel={handleCancelSetup}
                    onSuccess={handleDescribeSuccess}
                  />
                )}
                {reviewStep === 2 && (
                  <PrivacyDeclarationForm
                    systemKey={systemKey}
                    onCancel={handleCancelSetup}
                    onSuccess={handleDeclareSuccess}
                  />
                )}
                {reviewStep === 3 && (
                  <ReviewSystemForm
                    systemKey={systemKey}
                    onCancel={handleCancelSetup}
                    onSuccess={() => dispatch(changeReviewStep())}
                  />
                )}
                {reviewStep === 4 && (
                  <SuccessPage
                    systemKey={systemKey}
                    onAddNextSystem={() => {
                      dispatch(changeStep(5));
                      dispatch(changeReviewStep(1));
                    }}
                    onContinue={() => dispatch(changeStep())}
                  />
                )}
              </Stack>
            ) : null}
            {step === 6 ? <ViewYourDataMapPage /> : null}
          </Stack>
        </Stack>
      </Stack>
    </>
  );
};

export default ConfigWizardWalkthrough;
