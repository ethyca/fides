import { Box, Button, Divider, Stack } from "@fidesui/react";
import { useRouter } from "next/router";
import React, { useState } from "react";
import { CloseSolidIcon } from "~/features/common/Icon";
import Stepper from "../common/Stepper";
import AddSystemForm from "./AddSystemForm";
import { STEPS } from "./constants";
import DescribeSystemsForm from "./DescribeSystemsForm";
import { useUpdateOrganizationMutation } from "./organization.slice";
import OrganizationInfoForm from "./OrganizationInfoForm";

const ConfigWizardWalkthrough = () => {
  const router = useRouter();
  const [step, setStep] = useState<number>(1);
  const [fidesKey, setFidesKey] = useState("");
  const [updateOrganization] = useUpdateOrganizationMutation();

  const handleCancelSetup = () => {
    router.push("/");
  };

  const handleChangeStep = (formStep: number) => {
    // Save info between steps for submission to API with all info
    // or are they different api calls at each step?
    if (formStep && step !== STEPS.length) {
      setStep(formStep + 1);
    }
  };

  const handleFidesKey = (fidesKey: string) => {
    if (fidesKey) {
      setFidesKey(fidesKey);
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
          onClick={() => handleCancelSetup()}
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
              <OrganizationInfoForm
                handleChangeStep={handleChangeStep}
                handleFidesKey={handleFidesKey}
              />
            ) : null}
            {step === 2 ? (
              <AddSystemForm handleChangeStep={handleChangeStep} />
            ) : null}
            {step === 5 ? (
              <DescribeSystemsForm
                fidesKey={fidesKey}
                handleChangeStep={handleChangeStep}
                handleCancelSetup={handleCancelSetup}
              />
            ) : null}
          </Stack>
        </Stack>
      </Stack>
    </>
  );
};

export default ConfigWizardWalkthrough;
