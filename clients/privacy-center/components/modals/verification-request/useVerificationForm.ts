import { useToast } from "fidesui";
import { useFormik } from "formik";
import { Headers } from "headers-polyfill";
import { useCallback } from "react";

import { addCommonHeaders } from "~/common/CommonHeaders";
import { useLocalStorage } from "~/common/hooks";
import { ErrorToastOptions } from "~/common/toast-options";
import { useSettings } from "~/features/common/settings.slice";

import { ModalViews, VerificationType } from "../types";

export const useVerificationForm = ({
  onClose,
  requestId,
  setCurrentView,
  resetView,
  verificationType,
  successHandler,
}: {
  onClose: () => void;
  requestId: string;
  setCurrentView: (view: ModalViews) => void;
  resetView: ModalViews;
  verificationType: VerificationType;
  successHandler: () => void;
}) => {
  const settings = useSettings();
  const toast = useToast();
  const [, setVerificationCode] = useLocalStorage("verificationCode", "");
  const resetVerificationProcess = useCallback(() => {
    setCurrentView(resetView);
  }, [setCurrentView, resetView]);

  const formik = useFormik({
    initialValues: {
      code: "",
    },
    onSubmit: async (values) => {
      const body = {
        code: values.code,
      };

      const handleError = ({
        title,
        error,
      }: {
        title: string;
        error?: any;
      }) => {
        toast({
          title,
          description: error,
          ...ErrorToastOptions,
        });
        onClose();
      };
      try {
        const headers: Headers = new Headers();
        addCommonHeaders(headers, null);

        const response = await fetch(
          `${settings.FIDES_API_URL}/${verificationType}/${requestId}/verify`,
          {
            method: "POST",
            headers,
            body: JSON.stringify(body),
          },
        );
        const data = await response.json();

        if (!response.ok) {
          handleError({
            title: "An error occurred while verifying your identity",
            error: data?.detail,
          });
          return;
        }
        setVerificationCode(values.code);
        successHandler();
      } catch (error) {
        handleError({
          title:
            "An unhandled exception occurred while verifying your identity",
        });
      }
    },
    validate: (values) => {
      const errors: {
        code?: string;
      } = {};

      if (!values.code) {
        errors.code = "Required";
        return errors;
      }
      if (!values.code.match(/^\d+$/g)) {
        errors.code = "Verification code must be all numbers";
      }

      return errors;
    },
  });

  return { ...formik, resetVerificationProcess };
};
