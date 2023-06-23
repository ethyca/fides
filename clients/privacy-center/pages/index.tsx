import {
  Flex,
  Heading,
  Text,
  Stack,
  useToast,
  useDisclosure,
} from "@fidesui/react";
import React, { useEffect, useState } from "react";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { ConfigErrorToastOptions } from "~/common/toast-options";

import {
  usePrivacyRequestModal,
  PrivacyRequestModal,
} from "~/components/modals/privacy-request-modal/PrivacyRequestModal";
import {
  useConsentRequestModal,
  ConsentRequestModal,
} from "~/components/modals/consent-request-modal/ConsentRequestModal";
import { useGetIdVerificationConfigQuery } from "~/features/id-verification";
import PrivacyCard from "~/components/PrivacyCard";
import ConsentCard from "~/components/consent/ConsentCard";
import { useConfig } from "~/features/common/config.slice";
import { useSubscribeToPrivacyExperienceQuery } from "~/features/consent/hooks";
import { useAppSelector } from "~/app/hooks";
import { selectPrivacyExperience } from "~/features/consent/consent.slice";
import NoticeEmptyStateModal from "~/components/modals/NoticeEmptyStateModal";
import { selectIsNoticeDriven } from "~/features/common/settings.slice";

const Home: NextPage = () => {
  const router = useRouter();
  const config = useConfig();
  const [isVerificationRequired, setIsVerificationRequired] =
    useState<boolean>(false);
  const toast = useToast();
  const {
    isOpen: isPrivacyModalOpen,
    onClose: onPrivacyModalClose,
    onOpen: onPrivacyModalOpen,
    openAction,
    currentView: currentPrivacyModalView,
    setCurrentView: setCurrentPrivacyModalView,
    privacyRequestId,
    setPrivacyRequestId,
    successHandler: privacyModalSuccessHandler,
  } = usePrivacyRequestModal();

  const {
    isOpen: isConsentModalOpenConst,
    onOpen: onConsentModalOpen,
    onClose: onConsentModalClose,
    currentView: currentConsentModalView,
    setCurrentView: setCurrentConsentModalView,
    consentRequestId,
    setConsentRequestId,
    successHandler: consentModalSuccessHandler,
  } = useConsentRequestModal();
  let isConsentModalOpen = isConsentModalOpenConst;
  const getIdVerificationConfigQuery = useGetIdVerificationConfigQuery();

  // Subscribe to experiences just to see if there are any notices.
  // The subscription automatically handles skipping if overlay is not enabled
  useSubscribeToPrivacyExperienceQuery();
  const noticeEmptyStateModal = useDisclosure();
  const experience = useAppSelector(selectPrivacyExperience);
  const isNoticeDriven = useAppSelector(selectIsNoticeDriven);
  const emptyNotices =
    experience?.privacy_notices == null ||
    experience.privacy_notices.length === 0;

  const handleConsentCardOpen = () => {
    if (isNoticeDriven && emptyNotices) {
      noticeEmptyStateModal.onOpen();
    } else {
      onConsentModalOpen();
    }
  };

  useEffect(() => {
    if (getIdVerificationConfigQuery.isError) {
      // TODO(#2299): Use error utils from shared package.
      const errorData = (getIdVerificationConfigQuery.error as any)?.data;
      toast({
        description: errorData?.detail,
        ...ConfigErrorToastOptions,
      });
      return;
    }

    if (getIdVerificationConfigQuery.isSuccess) {
      setIsVerificationRequired(
        getIdVerificationConfigQuery.data.identity_verification_required
      );
    }
  }, [getIdVerificationConfigQuery, setIsVerificationRequired, toast]);

  const content: any = [];

  config.actions.forEach((action) => {
    content.push(
      <PrivacyCard
        key={action.title}
        title={action.title}
        policyKey={action.policy_key}
        iconPath={action.icon_path}
        description={action.description}
        onOpen={onPrivacyModalOpen}
      />
    );
  });

  if (config.includeConsent && config.consent) {
    content.push(
      <ConsentCard
        key="consentCard"
        title={config.consent.button.title}
        iconPath={config.consent.button.icon_path}
        description={config.consent.button.description}
        onOpen={handleConsentCardOpen}
      />
    );
    if (router.query?.showConsentModal === "true") {
      // manually override whether to show the consent modal given
      // the query param `showConsentModal`
      isConsentModalOpen = true;
    }
  }

  return (
    <main data-testid="home">
      <Stack align="center" py={["6", "16"]} px={5} spacing={14}>
        <Stack align="center" spacing={3}>
          <Heading
            fontSize={["3xl", "4xl"]}
            color="gray.600"
            fontWeight="semibold"
            textAlign="center"
            data-testid="heading"
          >
            {config.title}
          </Heading>

          <Text
            fontSize={["small", "medium"]}
            fontWeight="medium"
            maxWidth={624}
            textAlign="center"
            color="gray.600"
            data-testid="description"
          >
            {config.description}
          </Text>

          {config.description_subtext?.map((paragraph, index) => (
            <Text
              fontSize={["small", "medium"]}
              fontWeight="medium"
              maxWidth={624}
              textAlign="center"
              color="gray.600"
              data-testid={`description-${index}`}
              // eslint-disable-next-line react/no-array-index-key
              key={`description-${index}`}
            >
              {paragraph}
            </Text>
          ))}
        </Stack>
        <Flex m={-2} flexDirection={["column", "column", "row"]}>
          {content}
        </Flex>

        {config.addendum?.map((paragraph, index) => (
          <Text
            fontSize={["small", "medium"]}
            fontWeight="medium"
            maxWidth={624}
            color="gray.600"
            data-testid={`addendum-${index}`}
            // eslint-disable-next-line react/no-array-index-key
            key={`addendum-${index}`}
          >
            {paragraph}
          </Text>
        ))}
      </Stack>
      <PrivacyRequestModal
        isOpen={isPrivacyModalOpen}
        onClose={onPrivacyModalClose}
        openAction={openAction}
        currentView={currentPrivacyModalView}
        setCurrentView={setCurrentPrivacyModalView}
        privacyRequestId={privacyRequestId}
        setPrivacyRequestId={setPrivacyRequestId}
        isVerificationRequired={isVerificationRequired}
        successHandler={privacyModalSuccessHandler}
      />

      <ConsentRequestModal
        isOpen={isConsentModalOpen}
        onClose={onConsentModalClose}
        currentView={currentConsentModalView}
        setCurrentView={setCurrentConsentModalView}
        consentRequestId={consentRequestId}
        setConsentRequestId={setConsentRequestId}
        isVerificationRequired={isVerificationRequired}
        successHandler={consentModalSuccessHandler}
      />

      <NoticeEmptyStateModal
        isOpen={noticeEmptyStateModal.isOpen}
        onClose={noticeEmptyStateModal.onClose}
      />
    </main>
  );
};

export default Home;
