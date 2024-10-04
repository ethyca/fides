import {
  AntButton,
  Modal,
  ModalBody,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  Stack,
  useDisclosure,
  useToast,
} from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import InfoBox from "~/features/common/InfoBox";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { usePostPrivacyRequestMutation } from "~/features/privacy-requests/privacy-requests.slice";
import SubmitPrivacyRequestForm, {
  PrivacyRequestSubmitFormValues,
} from "~/features/privacy-requests/SubmitPrivacyRequestForm";
import { isErrorResult } from "~/types/errors";

const INFO_BOX_TITLE = "Warning: You are bypassing identity verification";
const INFO_BOX_TEXT =
  "You are bypassing Fides' built-in identity verification step. Please ensure that you are only entering information on behalf of a verified and approved user's privacy request.";

const SubmitPrivacyRequestModal = ({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) => {
  const [postPrivacyRequestMutationTrigger] = usePostPrivacyRequestMutation();

  const toast = useToast();

  const handleSubmit = async (values: PrivacyRequestSubmitFormValues) => {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const { is_verified, ...rest } = values;
    const customFields = rest.custom_privacy_request_fields
      ? Object.entries(rest.custom_privacy_request_fields)
          .map(([fieldName, fieldInfo]) =>
            fieldInfo.value ? { [fieldName]: fieldInfo } : {},
          )
          .reduce((acc, next) => ({ ...acc, ...next }), {})
      : undefined;
    const payload = {
      ...rest,
      custom_privacy_request_fields: customFields,
    };
    const result = await postPrivacyRequestMutationTrigger([payload]);
    if (isErrorResult(result)) {
      toast(
        errorToastParams(
          getErrorMessage(
            result.error,
            "An error occurred while creating this privacy request. Please try again",
          ),
        ),
      );
    } else {
      toast(successToastParams("Privacy request created"));
    }
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="2xl" isCentered>
      <ModalOverlay />
      <ModalContent
        data-testid="submit-request-modal"
        maxHeight="80%"
        overflowY="auto"
      >
        <ModalHeader>Create privacy request</ModalHeader>
        <ModalBody>
          <Stack spacing={4}>
            <InfoBox title={INFO_BOX_TITLE} text={INFO_BOX_TEXT} />
            <SubmitPrivacyRequestForm
              onSubmit={handleSubmit}
              onCancel={() => onClose()}
            />
          </Stack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

const SubmitPrivacyRequest = () => {
  const { onOpen, isOpen, onClose } = useDisclosure();
  return (
    <>
      <SubmitPrivacyRequestModal isOpen={isOpen} onClose={onClose} />
      <AntButton
        type="primary"
        size="small"
        onClick={onOpen}
        data-testid="submit-request-btn"
      >
        Create request
      </AntButton>
    </>
  );
};

export default SubmitPrivacyRequest;
