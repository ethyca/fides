import React, { useEffect, useState } from "react";
import type { NextPage } from "next";
import Head from "next/head";
import { Flex, Heading, Text, Stack, Image, useToast } from "@fidesui/react";
import { ConfigErrorToastOptions } from "~/common/toast-options";

import {
  usePrivactRequestModal,
  PrivacyRequestModal,
} from "~/components/modals/privacy-request-modal/PrivacyRequestModal";
import {
  useConsentRequestModal,
  ConsentRequestModal,
} from "~/components/modals/consent-request-modal/ConsentRequestModal";
import { hostUrl } from "~/constants";
import PrivacyCard from "../components/PrivacyCard";
import ConsentCard from "../components/ConsentCard";

import config from "../config/config.json";

const Home: NextPage = () => {
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
  } = usePrivactRequestModal();

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

  useEffect(() => {
    const getConfig = async () => {
      try {
        const response = await fetch(`${hostUrl}/id-verification/config/`, {
          headers: {
            "X-Fides-Source": "fidesops-privacy-center",
          },
        });
        const data = await response.json();
        if (!response.ok) {
          toast({
            description: data.detail,
            ...ConfigErrorToastOptions,
          });
        }
        setIsVerificationRequired(data.identity_verification_required);
      } catch (e) {
        toast(ConfigErrorToastOptions);
        // eslint-disable-next-line no-console
        console.error(e);
      }
    };
    getConfig();
  }, [setIsVerificationRequired, toast]);

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
        title={config.consent.title}
        iconPath={config.consent.icon_path}
        description={config.consent.description}
        onOpen={onConsentModalOpen}
      />
    );
  }

  return (
    <div>
      <Head>
        <title>Privacy Center</title>
        <meta name="description" content="Privacy Center" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

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
          />
        </Flex>
      </header>

      <main>
        <Stack align="center" py={["6", "16"]} px={5} spacing={8}>
          <Stack align="center" spacing={3}>
            <Heading
              fontSize={["3xl", "4xl"]}
              color="gray.600"
              fontWeight="semibold"
              textAlign="center"
            >
              {config.title}
            </Heading>
            <Text
              fontSize={["small", "medium"]}
              fontWeight="medium"
              maxWidth={624}
              textAlign="center"
              color="gray.600"
            >
              {config.description}
            </Text>
          </Stack>
          <Flex m={-2} flexDirection={["column", "column", "row"]}>
            {content}
          </Flex>
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
