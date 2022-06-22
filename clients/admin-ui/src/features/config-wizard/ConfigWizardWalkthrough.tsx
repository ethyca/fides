import { Box, Button, Divider, Stack } from "@fidesui/react";
import { useRouter } from "next/router";
import React, { useState } from "react";

import { CloseSolidIcon } from "~/features/common/Icon";

import HorizontalStepper from "../common/HorizontalStepper";
import Stepper from "../common/Stepper";
import AddSystemForm from "./AddSystemForm";
import { HORIZONTAL_STEPS, STEPS } from "./constants";
import DescribeSystemsForm from "./DescribeSystemsForm";
import OrganizationInfoForm from "./OrganizationInfoForm";
import PrivacyDeclarationForm from "./PrivacyDeclarationForm";
import ReviewSystemForm from "./ReviewSystemForm";
import ViewYourDataMapPage from "./ViewYourDataMapPage";

const ConfigWizardWalkthrough = () => {
  const router = useRouter();
  const [step, setStep] = useState<number>(1);
  const [reviewStep, setReviewStep] = useState<number>(1);
  const [systemFidesKey, setSystemFidesKey] = useState("");

  const handleCancelSetup = () => {
    router.push("/");
  };

  const handleChangeStep = (formStep: number) => {
    if (formStep && step !== STEPS.length) {
      setStep(formStep + 1);
    }
  };

  const handleChangeReviewStep = (rStep: number) => {
    if (rStep) {
      if (rStep === 4) {
        setReviewStep(1);
      } else {
        setReviewStep(rStep + 1);
      }
    }
  };

  const handleSystemFidesKey = (key: string) => {
    if (key) {
      setSystemFidesKey(key);
    }
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
            <Box>
              <Stepper
                activeStep={step}
                setActiveStep={setStep}
                steps={STEPS}
              />
            </Box>
            {step === 1 ? (
              <OrganizationInfoForm handleChangeStep={handleChangeStep} />
            ) : null}
            {step === 2 ? (
              <AddSystemForm handleChangeStep={handleChangeStep} />
            ) : null}
            {step === 5 ? (
              <Stack direction="column">
                <HorizontalStepper
                  activeStep={reviewStep}
                  steps={HORIZONTAL_STEPS}
                />
                {reviewStep === 1 && (
                  <DescribeSystemsForm
                    handleChangeStep={handleChangeStep}
                    handleCancelSetup={handleCancelSetup}
                    handleChangeReviewStep={handleChangeReviewStep}
                    handleSystemFidesKey={handleSystemFidesKey}
                  />
                )}
                {reviewStep === 2 && (
                  <PrivacyDeclarationForm
                    handleCancelSetup={handleCancelSetup}
                    handleChangeReviewStep={handleChangeReviewStep}
                    systemFidesKey={systemFidesKey}
                  />
                )}
                {reviewStep === 3 && (
                  <ReviewSystemForm
                    handleCancelSetup={handleCancelSetup}
                    handleChangeStep={handleChangeStep}
                    handleChangeReviewStep={handleChangeReviewStep}
                    systemFidesKey={systemFidesKey}
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
