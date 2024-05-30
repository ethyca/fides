import { Button, Flex, Spacer, UseDisclosureReturn } from "fidesui";
import { useState } from "react";

import AddModal from "~/features/configure-consent/AddModal";
import BigQueryOverview from "~/features/integrations/bigqueryOverviewCopy";
import ConfigureIntegrationForm from "~/features/integrations/ConfigureIntegrationForm";
import IntegrationBox from "~/features/integrations/IntegrationBox";
import { AccessLevel, ConnectionType } from "~/types/api";

const BQ_PLACEHOLDER = {
  name: "Google BigQuery",
  key: "bq_placeholder",
  connection_type: ConnectionType.BIGQUERY,
  access: AccessLevel.READ,
  created_at: "",
};

const AddIntegrationModal = ({
  isOpen,
  onClose,
}: Pick<UseDisclosureReturn, "isOpen" | "onClose">) => {
  const [step, setStep] = useState(0);

  const onCancel = () => {
    setStep(0);
    onClose();
  };

  return (
    <AddModal
      isOpen={isOpen}
      onClose={onClose}
      title="Google BigQuery integration"
    >
      {step === 0 && (
        <>
          <IntegrationBox
            integration={BQ_PLACEHOLDER}
            onConfigureClick={() => setStep(1)}
          />
          <BigQueryOverview />
          <Flex>
            <Spacer />
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
          </Flex>
        </>
      )}
      {step === 1 && <ConfigureIntegrationForm onCancel={onCancel} />}
    </AddModal>
  );
};

export default AddIntegrationModal;
