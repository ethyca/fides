import React, { useEffect, useState } from "react";
import type { NextPage } from "next";
import { Flex, Heading, Text, Stack, Image, useToast } from "@fidesui/react";
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
import ConsentCard from "~/components/ConsentCard";
import { useConfig } from "~/features/common/config.slice";

const Home: NextPage = () => {
  console.log("render Home");
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
    isOpen: isConsentModalOpen,
    onOpen: onConsentModalOpen,
    onClose: onConsentModalClose,
    currentView: currentConsentModalView,
    setCurrentView: setCurrentConsentModalView,
    consentRequestId,
    setConsentRequestId,
    successHandler: consentModalSuccessHandler,
  } = useConsentRequestModal();

  const getIdVerificationConfigQuery = useGetIdVerificationConfigQuery();

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
        onOpen={onConsentModalOpen}
      />
    );
  }

  return (
    <div>
      <header>
        <Flex
          bg="gray.100"
          minHeight={14}
          p={1}
          width="100%"
          justifyContent="center"
          alignItems="center"
        >
          <Image
            src={config.logo_path}
            margin="8px"
            height="68px"
            alt="Logo"
            data-testid="logo"
          />
        </Flex>
      </header>

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
      </main>
    </div>
  );
};

export default Home;
