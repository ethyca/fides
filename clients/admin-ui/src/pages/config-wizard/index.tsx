import type { NextPage } from "next";

import { useAppSelector } from "~/app/hooks";
import Header from "~/features/common/Header";
import Layout from "~/features/common/Layout";
import { selectStep } from "~/features/config-wizard/config-wizard.slice";
import ConfigWizardWalkthrough from "~/features/config-wizard/ConfigWizardWalkthrough";
import Setup from "~/features/config-wizard/setup";

const ConfigWizard: NextPage = () => {
  const step = useAppSelector(selectStep);

  return step === 0 ? (
    <Layout title="Config Wizard" noPadding>
      <Setup />
    </Layout>
  ) : (
    <>
      <Header />
      <ConfigWizardWalkthrough />
    </>
  );
};

export default ConfigWizard;
