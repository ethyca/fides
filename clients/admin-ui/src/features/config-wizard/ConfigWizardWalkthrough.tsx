import { Box, Button, Divider, Stack } from "@fidesui/react";
import { useRouter } from "next/router";
import React, { useState } from "react";
import Stepper from "../common/Stepper";
import OrganizationInfoForm from "./OrganizationInfoForm";

const ConfigWizardWalkthrough = () => {
  const router = useRouter();
  const [step, setStep] = useState(null);

  const handleCancelSetup = () => {
    // Cancel
    // Save progress ?
    router.push("/");
  };

  const handleChangeStep = () => {
    // Step
  };

  return (
    // Unique header to wizard
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
              <Stepper activeStep={1} />
            </Box>
            <OrganizationInfoForm handleChangeStep={handleChangeStep} />
          </Stack>
        </Stack>
        <Stack bg="gray.50" maxW="40%"></Stack>
      </Stack>
    </>
  );
};

export default ConfigWizardWalkthrough;
