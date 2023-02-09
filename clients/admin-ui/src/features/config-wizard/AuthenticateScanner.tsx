import { Box } from "@fidesui/react";

import { useAppSelector } from "~/app/hooks";
import { ValidTargets } from "~/types/api";

import AuthenticateAwsForm from "./AuthenticateAwsForm";
import AuthenticateOktaForm from "./AuthenticateOktaForm";
import { selectAddSystemsMethod } from "./config-wizard.slice";
import LoadDataFlowScanner from "./LoadDataFlowScanner";
import { SystemMethods } from "./types";
import LoadWebScanner from "~/features/config-wizard/LoadWebScanner";

const AuthenticateScanner = () => {
  const infrastructure = useAppSelector(selectAddSystemsMethod);

  if (infrastructure === ValidTargets.WEB_SCANNER) {
    return (
      <Box width="100%">
        <LoadWebScanner />
      </Box>
    );
  }

  return (
    <Box w="40%">
      {infrastructure === ValidTargets.AWS ? <AuthenticateAwsForm /> : null}
      {infrastructure === ValidTargets.OKTA ? <AuthenticateOktaForm /> : null}
      {/*
       * Data flow scanner currently authenticates via fidesctl.toml, so there is not
       * an authentication step. However, to fit into the onboarding flow, it makes sense to
       * load this at the same time as authentication since the other authenticate forms also
       * show a loading screen. At least until each path has its own custom steps it goes through
       * (fides#1514)
       */}
      {infrastructure === SystemMethods.DATA_FLOW ? (
        <LoadDataFlowScanner />
      ) : null}
    </Box>
  );
};

export default AuthenticateScanner;
