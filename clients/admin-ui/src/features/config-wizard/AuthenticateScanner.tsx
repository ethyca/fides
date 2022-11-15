import React from "react";

import { useAppSelector } from "~/app/hooks";
import { ValidTargets } from "~/types/api";

import AuthenticateAwsForm from "./AuthenticateAwsForm";
import { selectAddSystemsMethod } from "./config-wizard.slice";
import LoadRuntimeScanner from "./LoadRuntimeScanner";
import { SystemMethods } from "./types";

// TODO(#577)
const AuthenticateOktaForm = () => null;

const AuthenticateScanner = () => {
  const infrastructure = useAppSelector(selectAddSystemsMethod);
  return (
    <>
      {infrastructure === ValidTargets.AWS ? <AuthenticateAwsForm /> : null}
      {infrastructure === ValidTargets.OKTA ? <AuthenticateOktaForm /> : null}
      {/*
       * Runtime scanner currently authenticates via fidesctl.toml, so there is not
       * an authentication step. However, to fit into the onboarding flow, it makes sense to
       * load this at the same time as authentication since the other authenticate forms also
       * show a loading screen. At least until each path has its own custom steps it goes through
       * (fides#1514)
       */}
      {infrastructure === SystemMethods.RUNTIME ? <LoadRuntimeScanner /> : null}
    </>
  );
};

export default AuthenticateScanner;
