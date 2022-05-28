import { Box, Button, Stack } from "@fidesui/react";
import React, { useState } from "react";
import Stepper from "../common/Stepper";
import OrganizationInfoForm from "./OrganizationInfoForm";

const ConfigWizardWalkthrough = () => {
  const [step, setStep] = useState(null);

  const handleCancelSetup = () => {
    // Cancel
  };

  const handleChangeStep = () => {
    // Step
  };

  return (
    <Stack>
      <Box>
        <Button bg="transparent" onClick={handleCancelSetup}>
          x Cancel setup
        </Button>
      </Box>
      <Stack direction={"row"} spacing="24px">
        <Box>
          <Stepper activeStep={step} />
        </Box>
        <OrganizationInfoForm handleChangeStep={handleChangeStep} />
      </Stack>
    </Stack>
  );
};

export default ConfigWizardWalkthrough;
