"use client";

import { Flex } from "fidesui";
import { useRouter } from "next/navigation";
import React from "react";

import { ModalViews, VerificationType } from "~/components/modals/types";

import VerificationForm from "../modals/verification-request/VerificationForm";

type VerificationPageProps = {
  requestId: string;
  actionIndex: number;
};

const VerificationPage = ({
  requestId,
  actionIndex,
}: VerificationPageProps) => {
  const router = useRouter();

  const handleClose = () => {
    router.push("/");
  };

  const handleSetCurrentView = (view: string) => {
    // If going back to form, navigate to form page
    if (view === "privacyRequest") {
      router.push(`/privacy-request/${actionIndex}`);
    }
  };

  const handleSuccess = () => {
    // Navigate to success page
    router.push(`/privacy-request/${actionIndex}/success`);
  };

  return (
    <Flex vertical gap="middle">
      <VerificationForm
        isOpen
        onClose={handleClose}
        requestId={requestId}
        setCurrentView={handleSetCurrentView}
        resetView={ModalViews.PrivacyRequest}
        verificationType={VerificationType.PrivacyRequest}
        successHandler={handleSuccess}
      />
    </Flex>
  );
};

export default VerificationPage;
