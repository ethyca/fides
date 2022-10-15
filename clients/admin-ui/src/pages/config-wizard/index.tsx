import type { NextPage } from "next";
import { useState } from "react";

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
    <Layout title="Config Wizard" noPadding>
      <Setup wizardStep={handleWizardStep} />
    </Layout>
  ) : (
    <>
      <Header />
      <ConfigWizardWalkthrough />
    </>
  );
};

export default ConfigWizard;
