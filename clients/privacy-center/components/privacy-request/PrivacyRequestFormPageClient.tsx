"use client";

import { useEffect, useState } from "react";

import { useGetIdVerificationConfigQuery } from "~/features/id-verification";

import PrivacyRequestFormPage from "./PrivacyRequestFormPage";

type PrivacyRequestFormPageClientProps = {
  actionIndex: string;
};

const PrivacyRequestFormPageClient = ({
  actionIndex,
}: PrivacyRequestFormPageClientProps) => {
  const parsedActionIndex = parseInt(actionIndex, 10);
  const [isVerificationRequired, setIsVerificationRequired] =
    useState<boolean>(false);
  const getIdVerificationConfigQuery = useGetIdVerificationConfigQuery();

  // Update verification requirement from API
  useEffect(() => {
    if (getIdVerificationConfigQuery.isSuccess) {
      setIsVerificationRequired(
        getIdVerificationConfigQuery.data.identity_verification_required,
      );
    }
  }, [getIdVerificationConfigQuery]);

  if (Number.isNaN(parsedActionIndex)) {
    return null;
  }

  return (
    <PrivacyRequestFormPage
      actionIndex={parsedActionIndex}
      isVerificationRequired={isVerificationRequired}
    />
  );
};

export default PrivacyRequestFormPageClient;
