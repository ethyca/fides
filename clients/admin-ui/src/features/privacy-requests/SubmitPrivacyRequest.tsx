import { Dropdown, Flex, Icons, Modal, useMessage } from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import InfoBox from "~/features/common/InfoBox";
import { MODAL_SIZE } from "~/features/common/modals/modal-sizes";
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

  const message = useMessage();

  const handleSubmit = async (values: PrivacyRequestSubmitFormValues) => {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const { is_verified, ...rest } = values;
    const customFields = rest.custom_privacy_request_fields
      ? Object.entries(rest.custom_privacy_request_fields)
          .map(([fieldName, fieldInfo]: [string, any]) =>
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
      message.error(
        getErrorMessage(
          result.error,
          "An error occurred while creating this privacy request. Please try again",
        ),
      );
    } else {
      message.success("Privacy request created");
    }
    onClose();
  };

  return (
    <Modal
      open={isOpen}
      onCancel={onClose}
      centered
      destroyOnHidden
      data-testid="submit-request-modal"
      width={MODAL_SIZE.md}
      title="Create privacy request"
      footer={null}
    >
      <Flex vertical gap="large">
        <InfoBox title={INFO_BOX_TITLE} text={INFO_BOX_TEXT} />
        <SubmitPrivacyRequestForm
          onSubmit={handleSubmit}
          onCancel={() => onClose()}
        />
      </Flex>
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
    <Modal
      open={isOpen}
      onCancel={onClose}
      centered
      destroyOnHidden
      title="Create a Privacy Request Link"
      footer={null}
    >
      <CopyPrivacyRequestLinkForm
        privacyCenterUrl={privacyCenterUrl}
        onSubmit={onClose}
        onCancel={onClose}
      />
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
      {hasPrivacyCenterUrl && (
        <PrivacyRequestLinkModal
          isOpen={createLinkOpen}
          onClose={handleClose}
          privacyCenterUrl={privacyCenterUrl}
        />
      )}
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
              icon: <Icons.Link />,
              onClick: handleCreateLinkOpen,
              disabled: !hasPrivacyCenterUrl,
            },
          ],
        }}
        icon={<Icons.ChevronDown />}
      >
        Create request
      </Dropdown.Button>
    </>
  );
};

export default SubmitPrivacyRequest;
