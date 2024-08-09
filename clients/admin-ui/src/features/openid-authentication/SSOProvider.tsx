import {
  Box,
  Button,
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
  const { onOpen, isOpen, onClose } = useDisclosure();
  const { isOpen: deleteIsOpen, onClose: onDeleteClose } = useDisclosure();
  const toast = useToast();

  const [deleteOpenIDProviderMutation] = useDeleteOpenIDProviderMutation();

  const handleDelete = async () => {
    const result = await deleteOpenIDProviderMutation(openIDProvider.id);
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      onDeleteClose();
      return;
    }

    toast(successToastParams(`OpenID Provider deleted successfully`));

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
        <Button
          size="sm"
          marginRight="12px"
          variant="outline"
          onClick={onDeleteClose}
          data-testid="remove-sso-provider-btn"
        >
          Remove
        </Button>
        <Button
          size="sm"
          marginRight="12px"
          variant="outline"
          onClick={onOpen}
          data-testid="edit-sso-provider-btn"
        >
          Edit
        </Button>
      </Box>
      <EditSSOProviderModal
        isOpen={isOpen}
        onClose={onClose}
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
