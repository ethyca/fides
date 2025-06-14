import { UseDisclosureReturn } from "fidesui";
import { useState } from "react";

import FormModal from "~/features/common/modals/FormModal";
import getIntegrationTypeInfo, {
  IntegrationTypeInfo,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import ConfigureIntegrationForm from "~/features/integrations/add-integration/ConfigureIntegrationForm";
import IntegrationTypeDetail from "~/features/integrations/add-integration/IntegrationTypeDetail";
import SelectIntegrationType from "~/features/integrations/add-integration/SelectIntegrationType";
import { SaasConnectionTypes } from "~/features/integrations/types/SaasConnectionTypes";
import useIntegrationOption from "~/features/integrations/useIntegrationOption";

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
    IntegrationModalStep.LIST_VIEW,
  );

  const [integrationType, setIntegrationType] = useState<IntegrationTypeInfo>();

  const connectionOption = useIntegrationOption(
    integrationType?.placeholder.connection_type,
    integrationType?.placeholder?.saas_config?.type as SaasConnectionTypes,
  );

  const { description } = getIntegrationTypeInfo(
    integrationType?.placeholder.connection_type,
  );

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
    <FormModal
      size="2xl"
      isOpen={isOpen}
      onClose={handleCancel}
      title={modalTitle}
    >
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
        <ConfigureIntegrationForm
          connectionOption={connectionOption!}
          onCancel={handleCancel}
          description={description}
        />
      )}
    </FormModal>
  );
};

export default AddIntegrationModal;
