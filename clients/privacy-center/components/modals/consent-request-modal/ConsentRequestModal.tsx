import { AntModal as Modal } from "fidesui";
import { useParams, useRouter } from "next/navigation";
import React, { useCallback, useState } from "react";

import { useLocalStorage } from "~/common/hooks";
import { useConfig } from "~/features/common/config.slice";

import { ModalViews, VerificationType } from "../types";
import VerificationForm from "../verification-request/VerificationForm";
import ConsentRequestForm from "./ConsentRequestForm";

export const useConsentRequestModal = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [currentView, setCurrentView] = useState<ModalViews>(
    ModalViews.ConsentRequest,
  );
  const router = useRouter();
  const [consentRequestId, setConsentRequestId] = useLocalStorage(
    "consentRequestId",
    "",
  );

  const params = useParams();
  const propertyPath = params?.propertyPath;

  const successHandler = useCallback(() => {
    let consentRoute = "/consent";
    if (propertyPath) {
      consentRoute = `/${propertyPath}/consent`;
    }
    router.push(consentRoute);
  }, [propertyPath, router]);

  const onOpen = () => {
    setCurrentView(ModalViews.ConsentRequest);
    setIsOpen(true);
  };

  const onClose = () => {
    setIsOpen(false);
    setCurrentView(ModalViews.ConsentRequest);
    setConsentRequestId("");
    router.push("/");
  };

  return {
    isOpen,
    onClose,
    onOpen,
    currentView,
    setCurrentView,
    consentRequestId,
    setConsentRequestId,
    successHandler,
  };
};

export type ConsentRequestModalProps = {
  isOpen: boolean;
  onClose: () => void;
  currentView: ModalViews;
  setCurrentView: (view: ModalViews) => void;
  consentRequestId: string;
  setConsentRequestId: (id: string) => void;
  isVerificationRequired: boolean;
  successHandler: () => void;
};

export const ConsentRequestModal = ({
  isOpen,
  onClose,
  currentView,
  setCurrentView,
  consentRequestId,
  setConsentRequestId,
  isVerificationRequired,
  successHandler,
}: ConsentRequestModalProps) => {
  const config = useConfig();

  const modalProps: Record<ModalViews, React.ComponentProps<typeof Modal>> = {
    identityVerification: {
      title: "Enter verification code",
      children: (
        <VerificationForm
          isOpen={isOpen}
          onClose={onClose}
          requestId={consentRequestId}
          setCurrentView={setCurrentView}
          resetView={ModalViews.ConsentRequest}
          verificationType={VerificationType.ConsentRequest}
          successHandler={successHandler}
        />
      ),
    },
    privacyRequest: {
      open: false,
    },
    requestSubmitted: {
      open: false,
    },
    consentRequest: {
      title: config.consent?.button.modalTitle || config.consent?.button.title,
      children: (
        <ConsentRequestForm
          isOpen={isOpen}
          onClose={onClose}
          setCurrentView={setCurrentView}
          setConsentRequestId={setConsentRequestId}
          isVerificationRequired={isVerificationRequired}
          successHandler={successHandler}
        />
      ),
    },
  };

  return (
    <Modal
      open={isOpen}
      footer={null}
      {...modalProps[currentView]}
      onCancel={onClose}
    />
  );
};
