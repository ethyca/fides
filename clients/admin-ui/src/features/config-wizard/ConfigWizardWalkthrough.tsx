import { Flex } from "fidesui";

import { useAppSelector } from "~/app/hooks";

import AddSystem from "./AddSystem";
import AuthenticateScanner from "./AuthenticateScanner";
import { selectStep } from "./config-wizard.slice";
import { OrganizationInfoForm } from "./OrganizationInfoForm";
import ScanResults from "./ScanResults";

const ConfigWizardWalkthrough = () => {
  const step = useAppSelector(selectStep);

  return (
    <Flex className="bg-white">
      <div className="flex w-full justify-start">
        {step === 1 ? <OrganizationInfoForm /> : null}
        {step === 2 ? <AddSystem /> : null}
        {step === 3 ? <AuthenticateScanner /> : null}
        {step === 4 ? (
          <div className="pr-10">
            <ScanResults />
          </div>
        ) : null}
      </div>
    </Flex>
  );
};

export default ConfigWizardWalkthrough;
