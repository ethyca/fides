"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import PrivacyRequestFormPage from "./PrivacyRequestFormPage";
import { useGetIdVerificationConfigQuery } from "~/features/id-verification";

type PrivacyRequestFormPageClientProps = {
  actionIndex: string;
  searchParams: URLSearchParams | null;
};

const PrivacyRequestFormPageClient = ({
  actionIndex,
  searchParams,
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

  if (isNaN(parsedActionIndex)) {
    return null;
  }

  return (
    <PrivacyRequestFormPage
      actionIndex={parsedActionIndex}
      searchParams={searchParams}
      isVerificationRequired={isVerificationRequired}
    />
  );
};

export default PrivacyRequestFormPageClient;
