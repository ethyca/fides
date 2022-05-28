import { Box, Button, Divider, Stack } from "@fidesui/react";
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
      <Divider orientation="horizontal" />
      <Stack direction={"row"} spacing="24px">
        <Box>
          <Stepper activeStep={1} />
        </Box>
        <OrganizationInfoForm handleChangeStep={handleChangeStep} />
      </Stack>
    </Stack>
  );
};

export default ConfigWizardWalkthrough;
