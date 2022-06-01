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
      <Box m={2} ml={6}>
        <Button bg="transparent" fontWeight="500" onClick={handleCancelSetup}>
          x Cancel setup
        </Button>
      </Box>
      <Divider orientation="horizontal" />
      <Stack direction={["column", "row"]}>
        <Stack mt={10} mb={10} maxW="60%">
          <Stack direction={"row"} spacing="24px">
            <Box>
              <Stepper activeStep={1} />
            </Box>
            <OrganizationInfoForm handleChangeStep={handleChangeStep} />
          </Stack>
        </Stack>
        <Stack maxW="40%">
          <Box bg="blue"> Right hand side</Box>
          {/* give this stack 50% width to split page, this stack holds tooltips */}
        </Stack>
      </Stack>
    </>
  );
};

export default ConfigWizardWalkthrough;
