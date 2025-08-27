import { AntButton as Button, AntModal as Modal } from "fidesui";
import React, { useCallback, useState } from "react";

import { useConfig } from "~/features/common/config.slice";

import { ModalViews, VerificationType } from "../types";
import VerificationForm from "../verification-request/VerificationForm";
import PrivacyRequestForm from "./PrivacyRequestForm";
import RequestSubmitted from "./RequestSubmitted";

export const usePrivacyRequestModal = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [openAction, setOpenAction] = useState<number | null>(null);
  const [currentView, setCurrentView] = useState<ModalViews>(
    ModalViews.PrivacyRequest,
  );
  const [privacyRequestId, setPrivacyRequestId] = useState<string>("");

  const onOpen = (action: number) => {
    setOpenAction(action);
    setIsOpen(true);
  };

  const onClose = () => {
    setIsOpen(false);
    setOpenAction(null);
    setCurrentView(ModalViews.PrivacyRequest);
    setPrivacyRequestId("");
  };

  const successHandler = useCallback(() => {
    setCurrentView(ModalViews.RequestSubmitted);
  }, [setCurrentView]);

  return {
    isOpen,
    onClose,
    onOpen,
    openAction,
    currentView,
    setCurrentView,
    privacyRequestId,
    setPrivacyRequestId,
    successHandler,
  };
};

export type RequestModalProps = {
  isOpen: boolean;
  onClose: () => void;
  openAction: number | null;
  currentView: ModalViews;
  setCurrentView: (view: ModalViews) => void;
  privacyRequestId: string;
  setPrivacyRequestId: (id: string) => void;
  isVerificationRequired: boolean;
  successHandler: () => void;
};

export const PrivacyRequestModal = ({
  isOpen,
  onClose,
  openAction,
  currentView,
  setCurrentView,
  privacyRequestId,
  setPrivacyRequestId,
  isVerificationRequired,
  successHandler,
}: RequestModalProps) => {
  const config = useConfig();
  const action =
    typeof openAction === "number" ? config.actions[openAction] : null;

  const modalProps: Record<ModalViews, React.ComponentProps<typeof Modal>> = {
    identityVerification: {
      title: "Enter verification code",
      children: (
        <VerificationForm
          isOpen={isOpen}
          onClose={onClose}
          requestId={privacyRequestId}
          setCurrentView={setCurrentView}
          resetView={ModalViews.PrivacyRequest}
          verificationType={VerificationType.PrivacyRequest}
          successHandler={successHandler}
        />
      ),
    },
    privacyRequest: {
      title: action?.title,
      children: (
        <PrivacyRequestForm
          onClose={onClose}
          openAction={openAction}
          setCurrentView={setCurrentView}
          setPrivacyRequestId={setPrivacyRequestId}
          isVerificationRequired={isVerificationRequired}
        />
      ),
    },
    requestSubmitted: {
      title: "Request submitted",
      children: <RequestSubmitted />,
      footer: (
        <Button type="primary" size="small" onClick={onClose}>
          Continue
        </Button>
      ),
    },
    consentRequest: {
      open: false,
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
