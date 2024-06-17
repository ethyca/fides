import { UseDisclosureReturn } from "fidesui";
import { useState } from "react";

import { useAppSelector } from "~/app/hooks";
import AddModal from "~/features/configure-consent/AddModal";
import { selectConnectionTypeState } from "~/features/connection-type";
import { IntegrationTypeInfo } from "~/features/integrations/add-integration/allIntegrationTypes";
import ConfigureIntegrationForm from "~/features/integrations/add-integration/ConfigureIntegrationForm";
import IntegrationTypeDetail from "~/features/integrations/add-integration/IntegrationTypeDetail";
import SelectIntegrationType from "~/features/integrations/add-integration/SelectIntegrationType";

enum IntegrationModalStep {
  LIST_VIEW = "list-view",
  DETAIL = "detail",
  FORM = "form",
}

const AddIntegrationModal = ({
  isOpen,
  onClose,
}: Pick<UseDisclosureReturn, "isOpen" | "onClose">) => {
  const [step, setStep] = useState<IntegrationModalStep>(
    IntegrationModalStep.LIST_VIEW
  );

  const [integrationType, setIntegrationType] = useState<IntegrationTypeInfo>();

  const { connectionOptions } = useAppSelector(selectConnectionTypeState);

  const connectionOption = connectionOptions.find(
    (opt) => opt.identifier === integrationType?.placeholder.connection_type
  );

  console.log(connectionOption);

  const handleCancel = () => {
    setStep(IntegrationModalStep.LIST_VIEW);
    setIntegrationType(undefined);
    onClose();
  };

  const handleDetailClick = (typeInfo: IntegrationTypeInfo) => {
    setStep(IntegrationModalStep.DETAIL);
    setIntegrationType(typeInfo);
  };

  const handleConfigure = (typeInfo: IntegrationTypeInfo) => {
    setStep(IntegrationModalStep.FORM);
    setIntegrationType(typeInfo);
  };

  const modalTitle = integrationType
    ? `${integrationType.placeholder.name} Integration`
    : "Add integration";

  return (
    <AddModal isOpen={isOpen} onClose={handleCancel} title={modalTitle}>
      {step === IntegrationModalStep.LIST_VIEW && (
        <SelectIntegrationType
          onCancel={handleCancel}
          onDetailClick={handleDetailClick}
          onConfigureClick={handleConfigure}
        />
      )}
      {step === IntegrationModalStep.DETAIL && (
        <IntegrationTypeDetail
          integrationType={integrationType}
          onConfigure={() => setStep(IntegrationModalStep.FORM)}
          onCancel={handleCancel}
        />
      )}
      {step === IntegrationModalStep.FORM && (
        <ConfigureIntegrationForm onCancel={handleCancel} />
      )}
    </AddModal>
  );
};

export default AddIntegrationModal;
