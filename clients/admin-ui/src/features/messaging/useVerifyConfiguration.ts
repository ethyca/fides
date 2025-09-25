import { AntMessage as message } from "fidesui";
import { useState } from "react";

import {
  isErrorResult,
  isErrorWithDetail,
  isErrorWithDetailArray,
} from "~/features/common/helpers";

import { messagingProviders } from "./constants";
import { useCreateTestConnectionMessageMutation } from "./messaging.slice";

export const useVerifyConfiguration = () => {
  const [createTestMessage] = useCreateTestConnectionMessageMutation();
  const [isVerifying, setIsVerifying] = useState(false);
  type VerificationMeta = { timestamp: string; success: boolean };
  const [verifiedConfigs, setVerifiedConfigs] = useState<
    Record<string, VerificationMeta>
  >({});

  // Helper function to extract error message using the same logic as useAPIHelper
  const getErrorMessage = (error: any) => {
    let errorMsg = "An unexpected error occurred. Please try again.";
    if (isErrorWithDetail(error)) {
      errorMsg = error.data.detail;
    } else if (isErrorWithDetailArray(error)) {
      errorMsg = error.data.detail[0]?.msg ?? errorMsg;
    }
    return errorMsg;
  };

  const verifyConfiguration = async (serviceType: string) => {
    setIsVerifying(true);
    try {
      const isSMSProvider = serviceType === messagingProviders.twilio_text;

      const result = await createTestMessage({
        service_type: serviceType,
        details: {
          to_identity: isSMSProvider
            ? { phone_number: "+15551234567" }
            : { email: "test@example.com" },
        },
      });

      if (isErrorResult(result)) {
        message.error(getErrorMessage(result.error));
        // Record failed attempt so UI stays on "Verify configuration"
        const timestamp = new Date().toISOString();
        setVerifiedConfigs((prev) => ({
          ...prev,
          [serviceType]: { timestamp, success: false },
        }));
        return false;
      }

      message.success("Configuration verified successfully!");
      const timestamp = new Date().toISOString();
      setVerifiedConfigs((prev) => ({
        ...prev,
        [serviceType]: { timestamp, success: true },
      }));
      return true;
    } catch (error) {
      message.error(getErrorMessage(error));
      return false;
    } finally {
      setIsVerifying(false);
    }
  };

  const isConfigurationVerified = (serviceType: string) => {
    return Boolean(verifiedConfigs[serviceType]?.success);
  };

  const getVerificationData = (serviceType: string) =>
    verifiedConfigs[serviceType];

  return {
    verifyConfiguration,
    isVerifying,
    isConfigurationVerified,
    getVerificationData,
  };
};
