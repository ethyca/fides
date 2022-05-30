import type { NextPage } from "next";
import React, { useState } from "react";
import Layout from "~/features/common/Layout";
import ConfigWizardWalkthrough from "~/features/config-wizard/ConfigWizardWalkthrough";
import Setup from "../../features/config-wizard/setup";

const ConfigWizard: NextPage = () => {
  const [configWizardStep, setConfigWizardStep] = useState(false);

  const handleWizardStep = (step: boolean) => {
    setConfigWizardStep(step);
  };

  return !configWizardStep ? (
    <Layout title="Config Wizard">
      <Setup wizardStep={handleWizardStep} />
    </Layout>
  ) : (
    <ConfigWizardWalkthrough />
  );
};

export default ConfigWizard;
