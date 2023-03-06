import { Box, Button, CloseSolidIcon, Divider, Stack } from "@fidesui/react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";

import AddSystem from "./AddSystem";
import AuthenticateScanner from "./AuthenticateScanner";
import { reset, selectStep } from "./config-wizard.slice";
import OrganizationInfoForm from "./OrganizationInfoForm";
import ScanResults from "./ScanResults";

const ConfigWizardWalkthrough = () => {
  const dispatch = useAppDispatch();
  const step = useAppSelector(selectStep);

  const handleCancelSetup = () => {
    dispatch(reset());
  };

  return (
    <>
      <Stack
        direction={["column", "row"]}
        bg="white"
        height="100vh"
        width="100%"
      >
        <Box display="flex" justifyContent="center" w="100%">
          {step === 1 ? <OrganizationInfoForm /> : null}
          {step === 2 ? <AddSystem /> : null}
          {step === 3 ? <AuthenticateScanner /> : null}
          {step === 4 ? (
            <Box pr={10}>
              <ScanResults />
            </Box>
          ) : null}
        </Box>
      </Stack>
    </>
  );
};

export default ConfigWizardWalkthrough;
