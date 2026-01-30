"use client";

import { Flex } from "fidesui";
import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";

import { ModalViews, VerificationType } from "~/components/modals/types";

import VerificationForm from "../modals/verification-request/VerificationForm";

type VerificationPageProps = {
  actionKey: string;
};

const VerificationPage = ({ actionKey }: VerificationPageProps) => {
  const router = useRouter();
  const [privacyRequestId, setPrivacyRequestId] = useState<string>("");

  const policyKey = decodeURIComponent(actionKey);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedId = sessionStorage.getItem("privacyRequestId");
      if (storedId) {
        setPrivacyRequestId(storedId);
      } else {
        // If no request ID, redirect back to form
        router.push(`/privacy-request/${encodeURIComponent(policyKey)}`);
      }
    }
  }, [policyKey, router]);

  if (!privacyRequestId) {
    return null;
  }

  const handleClose = () => {
    router.push("/");
  };

  const handleSetCurrentView = (view: string) => {
    // If going back to form, navigate to form page
    if (view === "privacyRequest") {
      router.push(`/privacy-request/${encodeURIComponent(policyKey)}`);
    }
  };

  const handleSuccess = () => {
    // Navigate to success page
    router.push(`/privacy-request/${encodeURIComponent(policyKey)}/success`);
  };

  return (
    <Flex vertical gap="middle">
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
