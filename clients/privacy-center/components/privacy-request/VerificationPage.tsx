"use client";

import { Flex } from "fidesui";
import { useParams, useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";

import { decodePolicyKey } from "~/common/policy-key";
import { ModalViews, VerificationType } from "~/components/modals/types";
import { useConfig } from "~/features/common/config.slice";
import { PrivacyRequestOption } from "~/types/config";

import VerificationForm from "../modals/verification-request/VerificationForm";

type VerificationPageProps = {
  actionKey: string;
};

const VerificationPage = ({ actionKey }: VerificationPageProps) => {
  const config = useConfig();
  const router = useRouter();
  const params = useParams();
  const propertyPath = params?.propertyPath as string | undefined;
  const basePath = propertyPath ? `/${propertyPath}` : "";
  const [privacyRequestId, setPrivacyRequestId] = useState<string>("");

  const decoded = decodePolicyKey(actionKey);
  const colonIndex = decoded.indexOf(":");
  const actionIndex =
    colonIndex !== -1 ? parseInt(decoded.slice(0, colonIndex), 10) : NaN;
  const policyKey =
    colonIndex !== -1 ? decoded.slice(colonIndex + 1) : decoded;
  const actions = config.actions ?? [];
  const action = (
    !Number.isNaN(actionIndex) &&
    actions[actionIndex]?.policy_key === policyKey
      ? actions[actionIndex]
      : actions.find((a) => a.policy_key === policyKey)
  ) as PrivacyRequestOption | undefined;

  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedId = sessionStorage.getItem("privacyRequestId");
      if (storedId) {
        setPrivacyRequestId(storedId);
      } else {
        router.push(`${basePath}/privacy-request/${actionKey}`);
      }
    }
  }, [actionKey, router, basePath]);

  if (!privacyRequestId) {
    return null;
  }

  const handleClose = () => {
    router.push(basePath || "/");
  };

  const handleSetCurrentView = (view: string) => {
    if (view === "privacyRequest") {
      router.push(`${basePath}/privacy-request/${actionKey}`);
    }
  };

  const handleSuccess = () => {
    router.push(`${basePath}/privacy-request/${actionKey}/success`);
  };

  return (
    <Flex vertical gap="medium" data-testid="verification-page">
      <VerificationForm
        isOpen
        onClose={handleClose}
        requestId={privacyRequestId}
        setCurrentView={handleSetCurrentView}
        resetView={ModalViews.PrivacyRequest}
        verificationType={VerificationType.PrivacyRequest}
        successHandler={handleSuccess}
        verificationTitle={action?.verification_title}
        verificationDescription={action?.verification_description}
        verificationSubmitButtonText={action?.verification_submit_button_text}
        verificationResendButtonText={action?.verification_resend_button_text}
      />
    </Flex>
  );
};

export default VerificationPage;
