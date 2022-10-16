import type { NextPage } from "next";
import { useState } from "react";
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { Flags } from "react-feature-flags";

import Custom404 from "../404";

import Header from "~/features/common/Header";
import Layout from "~/features/common/Layout";
import ConfigWizardWalkthrough from "~/features/config-wizard/ConfigWizardWalkthrough";

import Setup from "../../features/config-wizard/setup";

const ConfigWizard: NextPage = () => {
  const [configWizardStep, setConfigWizardStep] = useState(false);

  const handleWizardStep = (step: boolean) => {
    setConfigWizardStep(step);
  };

  return !configWizardStep ? (
    <Flags
    authorizedFlags={["configWizardFlag"]}
    renderOn={() => (
    <Layout title="Config Wizard" noPadding>
      <Setup wizardStep={handleWizardStep} />
    </Layout>
    )}
    renderOff={() => <Custom404 />}
    />
  ) : (
    <Flags
    authorizedFlags={["configWizardFlag"]}
    renderOn={() => (
      <>
        <Header />
        <ConfigWizardWalkthrough />
      </>
      )}
    renderOff={() => <Custom404 />}
    />
  );
};

export default ConfigWizard;
