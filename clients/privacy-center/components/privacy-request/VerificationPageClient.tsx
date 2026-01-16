"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import VerificationPage from "./VerificationPage";

type VerificationPageClientProps = {
  actionIndex: string;
};

const VerificationPageClient = ({
  actionIndex,
}: VerificationPageClientProps) => {
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

  return (
    <VerificationPage
      requestId={privacyRequestId}
      actionIndex={parsedActionIndex}
    />
  );
};

export default VerificationPageClient;
