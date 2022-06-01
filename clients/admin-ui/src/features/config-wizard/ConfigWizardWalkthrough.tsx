import { Box, Button, Divider, Stack } from "@fidesui/react";
import { useRouter } from "next/router";
import React, { useState } from "react";
import Stepper from "../common/Stepper";
import OrganizationInfoForm from "./OrganizationInfoForm";

const ConfigWizardWalkthrough = () => {
  const router = useRouter();
  const [step, setStep] = useState<number>(1);

  const handleCancelSetup = () => {
    // Save progress
    router.push("/");
  };

  const handleChangeStep = (formStep: number) => {
    // Save info between steps for submission to API with all info
    // or are they different api calls at each step?
    if (formStep && step !== 5) {
      setStep(formStep + 1);
    } else {
      return;
    }
    // Step
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
          x Cancel setup
        </Button>
      </Box>
      <Divider orientation="horizontal" />
      <Stack direction={["column", "row"]}>
        <Stack bg="white" height="100vh" maxW="60%">
          <Stack mt={10} mb={10} direction={"row"} spacing="24px">
            <Box>
              <Stepper activeStep={step} />
            </Box>
            {step === 1 ? (
              <OrganizationInfoForm
                handleChangeStep={(organizationStep: number) =>
                  handleChangeStep(organizationStep)
                }
              />
            ) : null}
          </Stack>
        </Stack>
      </Stack>
    </>
  );
};

export default ConfigWizardWalkthrough;
