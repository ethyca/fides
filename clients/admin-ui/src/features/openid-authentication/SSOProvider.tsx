import {
  AntButton,
  Box,
  ConfirmationModal,
  Image,
  Text,
  useDisclosure,
  useToast,
} from "fidesui";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import EditSSOProviderModal from "~/features/openid-authentication/EditSSOProviderModal";
import { useDeleteOpenIDProviderMutation } from "~/features/openid-authentication/openprovider.slice";
import { OpenIDProvider } from "~/types/api/models/OpenIDProvider";

const SSOProvider = ({
  openIDProvider,
}: {
  openIDProvider: OpenIDProvider;
}) => {
  const {
    onOpen: onEditOpen,
    isOpen: isEditOpen,
    onClose: onEditClose,
  } = useDisclosure();
  const {
    onOpen: onDeleteOpen,
    isOpen: deleteIsOpen,
    onClose: onDeleteClose,
  } = useDisclosure();
  const toast = useToast();

  const [deleteOpenIDProviderMutation] = useDeleteOpenIDProviderMutation();

  const handleDelete = async () => {
    const result = await deleteOpenIDProviderMutation(
      openIDProvider.identifier,
    );
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      onDeleteClose();
      return;
    }

    toast(successToastParams(`SSO provider deleted successfully`));

    onDeleteClose();
  };

  return (
    <Box
      alignItems="center"
      borderRadius="lg"
      borderWidth="1px"
      display="flex"
      height="74px"
      marginBottom="24px"
      padding={2}
    >
      <Box display="flex" alignItems="center">
        <Image
          src={`/images/oauth-login/${openIDProvider.provider}.svg`}
          alt={`${openIDProvider.provider} icon`}
          width="40px"
          height="40px"
        />
        <Box display="flex" flexDirection="column">
          <Text fontSize="medium" fontWeight="bold" marginLeft="16px">
            {openIDProvider.name}
          </Text>
          <Text fontSize="medium" marginLeft="16px">
            {openIDProvider.identifier}
          </Text>
        </Box>
      </Box>
      <Box flexGrow={1} display="flex" justifyContent="flex-end">
        <AntButton
          className="mr-3"
          onClick={onDeleteOpen}
          data-testid="remove-sso-provider-btn"
        >
          Remove
        </AntButton>
        <AntButton
          className="mr-3"
          onClick={onEditOpen}
          data-testid="edit-sso-provider-btn"
        >
          Edit
        </AntButton>
      </Box>
      <EditSSOProviderModal
        isOpen={isEditOpen}
        onClose={onEditClose}
        openIDProvider={openIDProvider}
      />
      <ConfirmationModal
        isOpen={deleteIsOpen}
        onClose={onDeleteClose}
        onConfirm={handleDelete}
        title="Remove SSO provider"
        message={
          <Text>
            You are about to permanently remove this SSO provider. Are you sure
            you would like to continue?
          </Text>
        }
      />
    </Box>
  );
};

export default SSOProvider;
