"use client";

import { useMessage } from "fidesui";
import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";

import { useConfig } from "~/features/common/config.slice";
import { useGetIdVerificationConfigQuery } from "~/features/id-verification";

import PrivacyRequestForm from "../modals/privacy-request-modal/PrivacyRequestForm";

type PrivacyRequestFormPageProps = {
  actionIndex: string;
};

const PrivacyRequestFormPage = ({
  actionIndex,
}: PrivacyRequestFormPageProps) => {
  const config = useConfig();
  const router = useRouter();
  const parsedActionIndex = parseInt(actionIndex, 10);
  const [isVerificationRequired, setIsVerificationRequired] =
    useState<boolean>(false);
  const getIdVerificationConfigQuery = useGetIdVerificationConfigQuery();

  const messageApi = useMessage();

  // Update verification requirement from API
  useEffect(() => {
    if (getIdVerificationConfigQuery.isSuccess) {
      setIsVerificationRequired(
        getIdVerificationConfigQuery.data.identity_verification_required,
      );
    }
  }, [getIdVerificationConfigQuery]);

  if (Number.isNaN(parsedActionIndex)) {
    messageApi.error(
      `Invalid action index "${actionIndex}" for privacy request`,
    );
    router.push("/");
  }

  const action = config.actions[parsedActionIndex];

  if (!action) {
    messageApi.error(
      `Invalid action index "${actionIndex}" for privacy request`,
    );
    router.push("/");
  }

  const handleExit = () => {
    router.push("/");
  };

  const handleSetCurrentView = (view: string) => {
    // Navigate to verification page
    if (view === "identityVerification") {
      router.push(`/privacy-request/${parsedActionIndex}/verify`);
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
    router.push(`/privacy-request/${parsedActionIndex}/success`);
  };

  return (
    <PrivacyRequestForm
      onExit={handleExit}
      openAction={parsedActionIndex}
      setCurrentView={handleSetCurrentView}
      setPrivacyRequestId={handleSetPrivacyRequestId}
      isVerificationRequired={isVerificationRequired}
      onSuccessWithoutVerification={handleSuccessWithoutVerification}
    />
  );
};

export default PrivacyRequestFormPage;
