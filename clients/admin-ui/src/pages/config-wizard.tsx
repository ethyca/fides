import type { NextPage } from "next";

import Setup from "../features/config-wizard/Setup";
// import ConfigWizardModal from "../features/config-wizard/ConfigWizardModal"

const ConfigWizard: NextPage = () => (
    // step 0
    <Setup />

    // wizard initiated
    // <ConfigWizardModal />
  );

export default ConfigWizard;
