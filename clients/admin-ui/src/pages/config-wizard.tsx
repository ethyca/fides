import type { NextPage } from "next";
import Setup from "../features/config-wizard/setup";
// import ConfigWizardModal from "./config-wizard-modal"

const ConfigWizard: NextPage = () => {
  return (
    // step 0
    <Setup />

    // wizard initiated
    // <ConfigWizardModal />
  );
};

export default ConfigWizard;
