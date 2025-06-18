import { AntButton as Button, UseDisclosureReturn } from "fidesui";
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
  const [previousStep, setPreviousStep] = useState<IntegrationModalStep | null>(
    null,
  );

  const [integrationType, setIntegrationType] = useState<IntegrationTypeInfo>();
  const [formState, setFormState] = useState<{
    dirty: boolean;
    isValid: boolean;
    submitForm: () => void;
    loading: boolean;
  } | null>(null);

  const connectionOption = useIntegrationOption(
    integrationType?.placeholder.connection_type,
    integrationType?.placeholder?.saas_config?.type as SaasConnectionTypes,
  );

  const { description } = getIntegrationTypeInfo(
    integrationType?.placeholder.connection_type,
    integrationType?.placeholder.saas_config?.type,
  );

  const handleCancel = () => {
    setStep(IntegrationModalStep.LIST_VIEW);
    setPreviousStep(null);
    setIntegrationType(undefined);
    setFormState(null);
    onClose();
  };

  const handleSelectIntegration = (typeInfo: IntegrationTypeInfo) => {
    setIntegrationType(typeInfo);
  };

  const handleNext = () => {
    if (step === IntegrationModalStep.LIST_VIEW && integrationType) {
      setPreviousStep(IntegrationModalStep.LIST_VIEW);
      setStep(IntegrationModalStep.FORM);
    }
  };

  const handleDetailClick = (typeInfo: IntegrationTypeInfo) => {
    setStep(IntegrationModalStep.DETAIL);
    setIntegrationType(typeInfo);
  };

  const handleConfigure = () => {
    setPreviousStep(IntegrationModalStep.DETAIL);
    setStep(IntegrationModalStep.FORM);
  };

  const handleBack = () => {
    if (previousStep) {
      setStep(previousStep);
      setPreviousStep(null);
    }
  };

  const handleSave = () => {
    if (formState && formState.submitForm) {
      formState.submitForm();
    }
  };

  const modalTitle = integrationType
    ? `${integrationType.placeholder.name} Integration`
    : "Add integration";

  const renderFooterButtons = () => {
    if (step === IntegrationModalStep.LIST_VIEW) {
      return (
        <div className="flex w-full justify-between">
          <Button onClick={handleCancel}>Cancel</Button>
          <Button
            type="primary"
            onClick={handleNext}
            disabled={!integrationType}
          >
            Next
          </Button>
        </div>
      );
    }

    if (step === IntegrationModalStep.DETAIL) {
      return (
        <div className="flex w-full justify-between">
          <Button onClick={() => setStep(IntegrationModalStep.LIST_VIEW)}>
            Back
          </Button>
          <Button onClick={handleConfigure} type="primary">
            Next
          </Button>
        </div>
      );
    }

    if (step === IntegrationModalStep.FORM) {
      return (
        <div className="flex w-full justify-between">
          <Button onClick={handleBack}>Back</Button>
          <Button
            type="primary"
            onClick={handleSave}
            disabled={!formState || !formState.isValid || !formState.dirty}
            loading={formState?.loading}
            data-testid="save-btn"
          >
            Save
          </Button>
        </div>
      );
    }

    return null;
  };

  const modalFooter = renderFooterButtons();

  return (
    <FormModal
      isOpen={isOpen}
      onClose={handleCancel}
      title={modalTitle}
      scrollBehavior="inside"
      showCloseButton
      modalContentProps={{ height: "700px", maxWidth: "1010px" }}
      footer={modalFooter}
    >
      {step === IntegrationModalStep.LIST_VIEW && (
        <SelectIntegrationType
          selectedIntegration={integrationType}
          onSelectIntegration={handleSelectIntegration}
          onDetailClick={handleDetailClick}
        />
      )}
      {step === IntegrationModalStep.DETAIL && (
        <IntegrationTypeDetail
          integrationType={integrationType}
          onConfigure={handleConfigure}
        />
      )}
      {step === IntegrationModalStep.FORM && (
        <ConfigureIntegrationForm
          connectionOption={connectionOption!}
          onCancel={handleCancel}
          description={description}
          onFormStateChange={setFormState}
        />
      )}
    </FormModal>
  );
};

export default AddIntegrationModal;
