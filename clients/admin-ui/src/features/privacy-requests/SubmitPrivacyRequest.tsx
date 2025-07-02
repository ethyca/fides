import {
  AntDropdown as Dropdown,
  ChevronDownIcon,
  LinkIcon,
  Modal,
  ModalBody,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  Stack,
  useToast,
} from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import InfoBox from "~/features/common/InfoBox";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useGetFidesCloudConfigQuery } from "~/features/plus/plus.slice";
import { usePostPrivacyRequestMutation } from "~/features/privacy-requests/privacy-requests.slice";
import SubmitPrivacyRequestForm, {
  CopyPrivacyRequestLinkForm,
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

const PrivacyRequestLinkModal = ({
  isOpen,
  onClose,
  privacyCenterUrl,
}: {
  isOpen: boolean;
  onClose: () => void;
  privacyCenterUrl: string;
}) => {
  return (
    <Modal size="md" isOpen={isOpen} onClose={onClose}>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Create a Privacy Request Link</ModalHeader>
        <ModalBody>
          <Stack spacing={4} />
          <CopyPrivacyRequestLinkForm
            privacyCenterUrl={privacyCenterUrl}
            onSubmit={onClose}
            onCancel={onClose}
          />
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

const SubmitPrivacyRequest = () => {
  const [state, setState] = useState<
    "closed" | "create-link" | "submit-request"
  >("closed");

  const createLinkOpen = state === "create-link";
  const submitRequestOpen = state === "submit-request";
  const handleSubmitRequestOpen = () => setState("submit-request");
  const handleCreateLinkOpen = () => setState("create-link");
  const handleClose = () => setState("closed");

  const { data } = useGetFidesCloudConfigQuery();
  const privacyCenterUrl = (data?.privacy_center_url ?? "").trim();
  const hasPrivacyCenterUrl = privacyCenterUrl.length > 0;

  return (
    <>
      {hasPrivacyCenterUrl ? (
        <PrivacyRequestLinkModal
          isOpen={createLinkOpen}
          onClose={handleClose}
          privacyCenterUrl={privacyCenterUrl}
        />
      ) : null}
      <SubmitPrivacyRequestModal
        isOpen={submitRequestOpen}
        onClose={handleClose}
      />
      <Dropdown.Button
        type="primary"
        onClick={handleSubmitRequestOpen}
        data-testid="submit-request-btn"
        menu={{
          items: [
            {
              label: "Create request link",
              key: "create-request-link",
              icon: <LinkIcon />,
              onClick: handleCreateLinkOpen,
              disabled: !hasPrivacyCenterUrl,
            },
          ],
        }}
        icon={<ChevronDownIcon />}
      >
        Create request
      </Dropdown.Button>
    </>
  );
};

export default SubmitPrivacyRequest;
