import { Box, Button, CloseSolidIcon, Divider, Stack } from "@fidesui/react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";

import AddSystem from "./AddSystem";
import AuthenticateScanner from "./AuthenticateScanner";
import { reset, selectStep } from "./config-wizard.slice";
import OrganizationInfoForm from "./OrganizationInfoForm";
import ScanResults from "./ScanResults";

const ConfigWizardWalkthrough = () => {
  const dispatch = useAppDispatch();
  const step = useAppSelector(selectStep);
  const features = useFeatures();

  const handleCancelSetup = () => {
    dispatch(reset());
  };

  return (
    <>
      {!features.flags.navV2 && (
        <>
          <Box bg="white">
            <Button
              bg="transparent"
              fontWeight="500"
              m={2}
              ml={6}
              onClick={handleCancelSetup}
            >
              <CloseSolidIcon width="17px" /> Cancel setup
            </Button>
          </Box>
          <Divider orientation="horizontal" />
        </>
      )}
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
