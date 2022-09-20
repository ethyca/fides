import { Box, Button, Divider, Stack } from "@fidesui/react";
import { useRouter } from "next/router";
import React from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { CloseSolidIcon } from "~/features/common/Icon";
import DescribeSystemsForm from "~/features/system/DescribeSystemsForm";
import PrivacyDeclarationForm from "~/features/system/PrivacyDeclarationForm";
import ReviewSystemForm from "~/features/system/ReviewSystemForm";
import SystemRegisterSuccess from "~/features/system/SystemRegisterSuccess";
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
  selectSystemToCreate,
  setSystemToCreate,
} from "./config-wizard.slice";
import { HORIZONTAL_STEPS, STEPS } from "./constants";
import OrganizationInfoForm from "./OrganizationInfoForm";
import ScanResultsForm from "./ScanResultsForm";
import ViewYourDataMapPage from "./ViewYourDataMapPage";

const ConfigWizardWalkthrough = () => {
  const router = useRouter();

  const step = useAppSelector(selectStep);
  const reviewStep = useAppSelector(selectReviewStep);
  const dispatch = useAppDispatch();
  const system = useAppSelector(selectSystemToCreate);

  const handleCancelSetup = () => {
    router.push("/");
  };

  const handleSuccess = (values: System) => {
    dispatch(setSystemToCreate(values));
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
                    onSuccess={handleSuccess}
                    abridged
                  />
                )}
                {reviewStep === 2 && system && (
                  <PrivacyDeclarationForm
                    system={system}
                    onCancel={handleCancelSetup}
                    onSuccess={handleSuccess}
                    abridged
                  />
                )}
                {reviewStep === 3 && system && (
                  <ReviewSystemForm
                    system={system}
                    onCancel={handleCancelSetup}
                    onSuccess={() => dispatch(changeReviewStep())}
                    abridged
                  />
                )}
                {reviewStep === 4 && system && (
                  <SystemRegisterSuccess
                    system={system}
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
