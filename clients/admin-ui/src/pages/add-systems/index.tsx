import type { NextPage } from "next";
import { useEffect } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features.slice";
import Header from "~/features/common/Header";
import Layout from "~/features/common/Layout";
import {
  changeStep,
  selectStep,
} from "~/features/config-wizard/config-wizard.slice";
import ConfigWizardWalkthrough from "~/features/config-wizard/ConfigWizardWalkthrough";
import Setup from "~/features/config-wizard/setup";

const ConfigWizard: NextPage = () => {
  const dispatch = useAppDispatch();
  const features = useFeatures();
  const step = useAppSelector(selectStep);

  useEffect(() => {
    if (features.navV2) {
      // Add system form
      dispatch(changeStep(2));
    }
  }, [dispatch, features.navV2]);

  return (
    // eslint-disable-next-line react/jsx-no-useless-fragment
    <>
      {features.navV2 ? (
        <Layout title="Config Wizard">
          <ConfigWizardWalkthrough />
        </Layout>
      ) : (
        [
          step === 0 ? (
            <Layout title="Config Wizard">
              <Setup />
            </Layout>
          ) : (
            <>
              <Header />
              <ConfigWizardWalkthrough />
            </>
          ),
        ]
      )}
    </>
  );
};

export default ConfigWizard;
