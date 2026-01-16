"use client";

import { Flex } from "fidesui";
import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";

import { ModalViews, VerificationType } from "~/components/modals/types";

import VerificationForm from "../modals/verification-request/VerificationForm";

type VerificationPageProps = {
  actionIndex: string;
};

const VerificationPage = ({ actionIndex }: VerificationPageProps) => {
  const router = useRouter();
  const parsedActionIndex = parseInt(actionIndex, 10);
  const [privacyRequestId, setPrivacyRequestId] = useState<string>("");

  // Get request ID from sessionStorage
  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedId = sessionStorage.getItem("privacyRequestId");
      if (storedId) {
        setPrivacyRequestId(storedId);
      } else {
        // If no request ID, redirect back to form
        router.push(`/privacy-request/${parsedActionIndex}`);
      }
    }
  }, [parsedActionIndex, router]);

  if (Number.isNaN(parsedActionIndex) || !privacyRequestId) {
    return null;
  }

  const handleClose = () => {
    router.push("/");
  };

  const handleSetCurrentView = (view: string) => {
    // If going back to form, navigate to form page
    if (view === "privacyRequest") {
      router.push(`/privacy-request/${parsedActionIndex}`);
    }
  };

  const handleSuccess = () => {
    // Navigate to success page
    router.push(`/privacy-request/${parsedActionIndex}/success`);
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
