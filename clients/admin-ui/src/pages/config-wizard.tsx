import type { NextPage } from "next";
import ConfigWizardWalkthrough from "../features/config-wizard/ConfigWizardWalkthrough";
import Setup from "../features/config-wizard/setup";

const ConfigWizard: NextPage = () => (
  <>
    {/* step 0 */}
    <Setup />
    {/* wizard initiated */}
    <ConfigWizardWalkthrough />
  </>
);

export default ConfigWizard;
