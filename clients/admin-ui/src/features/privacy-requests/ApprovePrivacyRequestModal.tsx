import { Button, Flex, Modal, Typography } from "fidesui";
import React, { useCallback } from "react";

import { PrivacyRequestResponse } from "~/types/api";

import {
  getCustomFields,
  getOtherIdentities,
  getPrimaryIdentity,
} from "./dashboard/utils";
import { PrivacyRequestEntity } from "./types";

type ApproveModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onApproveRequest: () => Promise<any>;
  isLoading: boolean;
  subjectRequest: PrivacyRequestResponse | PrivacyRequestEntity;
};

const ApprovePrivacyRequestModal = ({
  isOpen,
  onClose,
  onApproveRequest,
  isLoading,
  subjectRequest,
}: ApproveModalProps) => {
  const {
    identity,
    identity_verified_at: identityVerifiedAt,
    custom_privacy_request_fields: customPrivacyRequestFields,
  } = subjectRequest;

  const primaryIdentity = getPrimaryIdentity(identity);
  const otherIdentities = getOtherIdentities(identity, primaryIdentity);
  const allIdentities = [
    ...(primaryIdentity ? [primaryIdentity] : []),
    ...otherIdentities,
  ];
  const customFields = getCustomFields(customPrivacyRequestFields);

  const handleSubmit = useCallback(() => {
    onApproveRequest().then(() => {
      onClose();
    });
  }, [onApproveRequest, onClose]);

  return (
    <Modal
      open={isOpen}
      onCancel={onClose}
      centered
      destroyOnHidden
      title="Privacy request approval"
      footer={
        <Flex className="w-full" gap={12}>
          <Button
            onClick={onClose}
            className="mr-3 flex-1"
            data-testid="cancel-btn"
          >
            Cancel
          </Button>
          <Button
            type="primary"
            data-testid="continue-btn"
            onClick={handleSubmit}
            loading={isLoading}
            className="flex-1"
          >
            Confirm
          </Button>
        </Flex>
      }
    >
      <Typography.Text type="secondary" size="sm" className="mb-4 block">
        Are you sure you want to approve this privacy request?
      </Typography.Text>
      <ul className="list-disc pl-5">
        {allIdentities.map((identityItem) => (
          <li key={identityItem.key}>
            <Flex align="flex-start">
              <Typography.Text strong size="sm" className="mr-2">
                {identityItem.label}:
              </Typography.Text>
              <Typography.Text
                type="secondary"
                size="sm"
                className="mr-2 font-medium"
              >
                {identityItem.value}
              </Typography.Text>
              ({identityVerifiedAt ? "Verified" : "Unverified"})
            </Flex>
          </li>
        ))}
        {customFields.map((field) => (
          <li key={field.key}>
            <Flex align="flex-start">
              <Typography.Text strong size="sm" className="mr-2">
                {field.label}:
              </Typography.Text>
              <Typography.Text
                type="secondary"
                size="sm"
                className="mr-2 font-medium"
              >
                {Array.isArray(field.value)
                  ? field.value.join(", ")
                  : String(field.value)}
              </Typography.Text>
              (Unverified)
            </Flex>
          </li>
        ))}
      </ul>
    </Modal>
  );
};

export default ApprovePrivacyRequestModal;
