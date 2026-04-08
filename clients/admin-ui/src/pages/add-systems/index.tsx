import type { NextPage } from "next";
import { useEffect } from "react";

import { useAppDispatch } from "~/app/hooks";
import Layout from "~/features/common/Layout";
import { SidePanel } from "~/features/common/SidePanel";
import { changeStep } from "~/features/config-wizard/config-wizard.slice";
import ConfigWizardWalkthrough from "~/features/config-wizard/ConfigWizardWalkthrough";

const ConfigWizard: NextPage = () => {
  const dispatch = useAppDispatch();

  useEffect(() => {
    dispatch(changeStep(2));
  }, [dispatch]);

  return (
    <>
      <SidePanel>
        <SidePanel.Identity title="Add systems" />
      </SidePanel>
      <Layout title="Add systems">
        <ConfigWizardWalkthrough />
      </Layout>
    </>
  );
};

export default ConfigWizard;
