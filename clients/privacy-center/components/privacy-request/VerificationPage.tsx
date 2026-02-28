"use client";

import { Flex } from "fidesui";
import { useParams, useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";

import { decodePolicyKey, encodePolicyKey } from "~/common/policy-key";
import { ModalViews, VerificationType } from "~/components/modals/types";

import VerificationForm from "../modals/verification-request/VerificationForm";

type VerificationPageProps = {
  actionKey: string;
};

const VerificationPage = ({ actionKey }: VerificationPageProps) => {
  const router = useRouter();
  const params = useParams();
  const propertyPath = params?.propertyPath as string | undefined;
  const basePath = propertyPath ? `/${propertyPath}` : "";
  const [privacyRequestId, setPrivacyRequestId] = useState<string>("");

  const policyKey = decodePolicyKey(actionKey);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedId = sessionStorage.getItem("privacyRequestId");
      if (storedId) {
        setPrivacyRequestId(storedId);
      } else {
        router.push(
          `${basePath}/privacy-request/${encodePolicyKey(policyKey)}`,
        );
      }
    }
  }, [policyKey, router, basePath]);

  if (!privacyRequestId) {
    return null;
  }

  const handleClose = () => {
    router.push(basePath || "/");
  };

  const handleSetCurrentView = (view: string) => {
    if (view === "privacyRequest") {
      router.push(`${basePath}/privacy-request/${encodePolicyKey(policyKey)}`);
    }
  };

  const handleSuccess = () => {
    router.push(
      `${basePath}/privacy-request/${encodePolicyKey(policyKey)}/success`,
    );
  };

  return (
    <Flex vertical gap="middle" data-testid="verification-page">
      <VerificationForm
        isOpen
        onClose={handleClose}
        requestId={privacyRequestId}
        setCurrentView={handleSetCurrentView}
        resetView={ModalViews.PrivacyRequest}
        verificationType={VerificationType.PrivacyRequest}
        successHandler={handleSuccess}
      />
    </Flex>
  );
};

export default VerificationPage;
