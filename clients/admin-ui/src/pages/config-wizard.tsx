import type { NextPage } from "next";
import ConfigWizardModal from "../features/config-wizard/ConfigWizardModal";
import Setup from "../features/config-wizard/setup";

const ConfigWizard: NextPage = () => (
  <>
    {/* step 0 */}
    <Setup />
    {/* wizard initiated */}
    <ConfigWizardModal />
  </>
);

export default ConfigWizard;
