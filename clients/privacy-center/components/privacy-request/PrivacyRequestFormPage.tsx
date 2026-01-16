"use client";

import { useRouter } from "next/navigation";
import React from "react";

import { useConfig } from "~/features/common/config.slice";
import { PrivacyRequestOption } from "~/types/config";

import PrivacyRequestForm from "../modals/privacy-request-modal/PrivacyRequestForm";

type PrivacyRequestFormPageProps = {
  actionIndex: number;
  isVerificationRequired: boolean;
};

const PrivacyRequestFormPage = ({
  actionIndex,
  isVerificationRequired,
}: PrivacyRequestFormPageProps) => {
  const config = useConfig();
  const router = useRouter();

  const action = config.actions[actionIndex] as
    | PrivacyRequestOption
    | undefined;

  if (!action) {
    router.push("/");
    return null;
  }

  const handleClose = () => {
    router.push("/");
  };

  const handleSetCurrentView = (view: string) => {
    // Navigate to verification page
    if (view === "identityVerification") {
      router.push(`/privacy-request/${actionIndex}/verify`);
    }
  };

  const handleSetPrivacyRequestId = (id: string) => {
    // Store the request ID in sessionStorage for the verification page
    if (typeof window !== "undefined") {
      sessionStorage.setItem("privacyRequestId", id);
    }
  };

  const handleSuccessWithoutVerification = () => {
    // Navigate to success page when verification is not required
    router.push(`/privacy-request/${actionIndex}/success`);
  };

  return (
    <PrivacyRequestForm
      onClose={handleClose}
      openAction={actionIndex}
      setCurrentView={handleSetCurrentView}
      setPrivacyRequestId={handleSetPrivacyRequestId}
      isVerificationRequired={isVerificationRequired}
      onSuccessWithoutVerification={handleSuccessWithoutVerification}
    />
  );
};

export default PrivacyRequestFormPage;
