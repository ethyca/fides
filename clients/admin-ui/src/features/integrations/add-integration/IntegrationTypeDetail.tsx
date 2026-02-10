import { Button, Modal, useMessage } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { useDeleteConnectorTemplateMutation } from "~/features/connector-templates/connector-template.slice";
import { IntegrationTypeInfo } from "~/features/integrations/add-integration/allIntegrationTypes";
import IntegrationBox from "~/features/integrations/IntegrationBox";
import { SaasConnectionTypes } from "~/features/integrations/types/SaasConnectionTypes";
import useIntegrationOption from "~/features/integrations/useIntegrationOption";

const IntegrationTypeDetail = ({
  integrationType,
  onConfigure,
}: {
  integrationType?: IntegrationTypeInfo;
  onConfigure: () => void;
}) => {
  const connectionOption = useIntegrationOption(
    integrationType?.placeholder.connection_type,
    integrationType?.placeholder.saas_config?.type as SaasConnectionTypes,
  );

  const [modalApi, modalContext] = Modal.useModal();
  const messageApi = useMessage();
  const [deleteConnectorTemplate] = useDeleteConnectorTemplateMutation();

  const showRemoveButton =
    !!connectionOption?.custom &&
    !!connectionOption?.default_connector_available;

  const handleRemoveCustomIntegration = () => {
    modalApi.confirm({
      title: "Remove",
      icon: null,
      content: (
        <>
          This will remove the custom integration template and update all
          systems and connections that use it. All instances will revert to the
          Fides-provided default integration template.
          <br />
          <br />
          This change applies globally and cannot be undone. Are you sure you
          want to proceed?
        </>
      ),
      okText: "Remove",
      okButtonProps: { danger: true },
      centered: true,
      onOk: async () => {
        if (connectionOption?.identifier) {
          try {
            await deleteConnectorTemplate(connectionOption.identifier).unwrap();
          } catch (error) {
            messageApi.error(getErrorMessage(error as any));
          }
        }
      },
    });
  };

  return (
    <>
      {modalContext}
      <IntegrationBox
        integration={integrationType?.placeholder}
        integrationTypeInfo={integrationType}
        onConfigureClick={onConfigure}
        otherButtons={
          showRemoveButton ? (
            <Button
              type="link"
              danger
              data-testid="remove-custom-integration-btn"
              onClick={handleRemoveCustomIntegration}
            >
              Remove
            </Button>
          ) : undefined
        }
      />
      {integrationType?.overview}
    </>
  );
};

export default IntegrationTypeDetail;
