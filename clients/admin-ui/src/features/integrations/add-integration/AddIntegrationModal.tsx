import { Button, Flex, Modal } from "fidesui";
import { useState } from "react";

import getIntegrationTypeInfo, {
  IntegrationTypeInfo,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import ConfigureIntegrationForm from "~/features/integrations/add-integration/ConfigureIntegrationForm";
import IntegrationTypeDetail from "~/features/integrations/add-integration/IntegrationTypeDetail";
import SelectIntegrationType, {
  useIntegrationFilters,
} from "~/features/integrations/add-integration/SelectIntegrationType";
import { SaasConnectionTypes } from "~/features/integrations/types/SaasConnectionTypes";
import useIntegrationOption from "~/features/integrations/useIntegrationOption";

enum IntegrationModalStep {
  LIST_VIEW = "list-view",
  DETAIL = "detail",
  FORM = "form",
}

interface AddIntegrationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface FormState {
  dirty: boolean;
  isValid: boolean;
  submitForm: () => void;
  loading: boolean;
}

const AddIntegrationModal = ({ isOpen, onClose }: AddIntegrationModalProps) => {
  const [step, setStep] = useState<IntegrationModalStep>(
    IntegrationModalStep.LIST_VIEW,
  );
  const [previousStep, setPreviousStep] = useState<IntegrationModalStep | null>(
    null,
  );

  const [integrationType, setIntegrationType] = useState<IntegrationTypeInfo>();
  const [formState, setFormState] = useState<FormState | null>(null);

  const { filterBar, filteredTypes, isFiltering } = useIntegrationFilters();

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

  const handleIntegrationClick = (typeInfo: IntegrationTypeInfo) => {
    setIntegrationType(typeInfo);
    setPreviousStep(IntegrationModalStep.LIST_VIEW);
    setStep(IntegrationModalStep.FORM);
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

  const modalTitle =
    integrationType && step !== IntegrationModalStep.LIST_VIEW
      ? `${integrationType.placeholder.name} integration`
      : "Select an integration";

  const renderFooter = () => {
    if (step === IntegrationModalStep.LIST_VIEW) {
      return null;
    }

    if (step === IntegrationModalStep.DETAIL) {
      return (
        <Flex justify="space-between" className="w-full">
          <Button onClick={() => setStep(IntegrationModalStep.LIST_VIEW)}>
            Back
          </Button>
          <Button
            onClick={handleConfigure}
            type="primary"
            data-testid="configure-modal-btn"
          >
            Next
          </Button>
        </Flex>
      );
    }

    if (step === IntegrationModalStep.FORM) {
      return (
        <Flex justify="space-between" className="w-full">
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
        </Flex>
      );
    }

    return null;
  };

  return (
    <Modal
      open={isOpen}
      onCancel={handleCancel}
      title={modalTitle}
      centered
      destroyOnHidden
      width={1010}
      footer={renderFooter()}
      styles={{
        content: {
          height: 700,
          display: "flex",
          flexDirection: "column",
        },
        body: {
          flex: 1,
          padding: 0,
          display: "flex",
          flexDirection: "column",
          minHeight: 0,
        },
      }}
      data-testid="add-modal-content"
    >
      {step === IntegrationModalStep.LIST_VIEW && (
        <>
          <Flex className="px-6 py-4">{filterBar}</Flex>
          <Flex
            vertical
            flex={1}
            className="px-6 pb-4"
            style={{ overflowY: "auto" }}
          >
            <SelectIntegrationType
              filteredTypes={filteredTypes}
              isFiltering={isFiltering}
              onIntegrationClick={handleIntegrationClick}
              onDetailClick={handleDetailClick}
            />
          </Flex>
        </>
      )}
      {step === IntegrationModalStep.DETAIL && (
        <Flex vertical flex={1} className="p-6" style={{ overflowY: "auto" }}>
          <IntegrationTypeDetail
            integrationType={integrationType}
            onConfigure={handleConfigure}
          />
        </Flex>
      )}
      {step === IntegrationModalStep.FORM && (
        <Flex vertical flex={1} className="p-6" style={{ overflowY: "auto" }}>
          <ConfigureIntegrationForm
            connectionOption={connectionOption!}
            onClose={handleCancel}
            description={description}
            onFormStateChange={setFormState}
          />
        </Flex>
      )}
    </Modal>
  );
};

export default AddIntegrationModal;
