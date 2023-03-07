import type { NextPage } from "next";
import { useEffect } from "react";

import { useAppDispatch } from "~/app/hooks";
import Layout from "~/features/common/Layout";
import {
  changeStep,
} from "~/features/config-wizard/config-wizard.slice";
import ConfigWizardWalkthrough from "~/features/config-wizard/ConfigWizardWalkthrough";

const ConfigWizard: NextPage = () => {
  const dispatch = useAppDispatch();

  useEffect(() => {
    // Add system form
    dispatch(changeStep(2));
  }, [dispatch]);

  return (
    <Layout title="Config Wizard">
      <ConfigWizardWalkthrough />
    </Layout>
  );
};

export default ConfigWizard;
