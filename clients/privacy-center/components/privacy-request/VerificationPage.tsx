"use client";

import { Flex } from "fidesui";
import { useParams, useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";

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
      />
    </Flex>
  );
};

export default VerificationPage;
