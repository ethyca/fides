import { Modal, useMessage } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { useDeleteConnectorTemplateMutation } from "~/features/connector-templates/connector-template.slice";
import { ConnectionSystemTypeMap } from "~/types/api";

/**
 * Hook for handling removal of custom integration templates.
 * Returns a handler function and modal context that should be rendered.
 *
 * @param connectionOption - The connection option to remove
 * @returns Object containing the remove handler and modal context element
 */
export const useRemoveCustomIntegration = (
  connectionOption?: ConnectionSystemTypeMap | null,
) => {
  const [modalApi, modalContext] = Modal.useModal();
  const messageApi = useMessage();
  const [deleteConnectorTemplate] = useDeleteConnectorTemplateMutation();

  const handleRemove = () => {
    const integrationName =
      connectionOption?.human_readable || "this integration";

    modalApi.confirm({
      title: "Remove custom integration template",
      icon: null,
      content: (
        <>
          You are about to remove the custom integration template for{" "}
          <strong>{integrationName}</strong>. The custom template will be
          permanently deleted from your workspace, and all systems and
          connections currently using this custom template will automatically
          revert to the standard Fides integration template. Your data and
          configuration settings will remain intact.
          <br />
          <br />
          This change cannot be undone. To restore the custom template later,
          you will need to upload it again.
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

  return {
    handleRemove,
    modalContext,
  };
};
