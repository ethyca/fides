import type { NextPage } from "next";
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { Flags } from "react-feature-flags";

import { useAppSelector } from "~/app/hooks";
import Header from "~/features/common/Header";
import Layout from "~/features/common/Layout";
import { selectStep } from "~/features/config-wizard/config-wizard.slice";
import ConfigWizardWalkthrough from "~/features/config-wizard/ConfigWizardWalkthrough";

import Setup from "../../features/config-wizard/setup";
import Custom404 from "../404";

const ConfigWizard: NextPage = () => {
  const step = useAppSelector(selectStep);

  return (
    <Flags
      authorizedFlags={["configWizardFlag"]}
      renderOn={() =>
        step === 0 ? (
          <Layout title="Config Wizard" noPadding>
            <Setup />
          </Layout>
        ) : (
          <>
            <Header />
            <ConfigWizardWalkthrough />
          </>
        )
      }
      renderOff={() => <Custom404 />}
    />
  );
};

export default ConfigWizard;
