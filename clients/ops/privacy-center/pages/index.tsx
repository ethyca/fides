import React, { useEffect, useState } from "react";
import type { NextPage } from "next";
import Head from "next/head";
import {
  Flex,
  Heading,
  Text,
  Stack,
  Alert,
  AlertIcon,
  AlertDescription,
  CloseButton,
  Image,
} from "@fidesui/react";

import {
  usePrivactRequestModal,
  PrivacyRequestModal,
} from "../components/modals/privacy-request-modal/PrivacyRequestModal";
import {
  useConsentRequestModal,
  ConsentRequestModal,
} from "../components/modals/consent-request-modal/ConsentRequestModal";
import PrivacyCard from "../components/PrivacyCard";
import ConsentCard from "../components/ConsentCard";
import type { AlertState } from "../types/AlertState";

import config from "../config/config.json";
import { hostUrl } from "../constants";

const Home: NextPage = () => {
  const [alert, setAlert] = useState<AlertState | null>(null);
  const [isVerificationRequired, setIsVerificationRequired] =
    useState<boolean>(false);
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
    if (alert?.status) {
      const closeAlertTimer = setTimeout(() => setAlert(null), 8000);
      return () => clearTimeout(closeAlertTimer);
    }
    return () => false;
  }, [alert]);

  useEffect(() => {
    const getConfig = async () => {
      const response = await fetch(`${hostUrl}/id-verification/config`, {
        headers: {
          "X-Fides-Source": "fidesops-privacy-center",
        },
      });
      const data = await response.json();
      setIsVerificationRequired(data.identity_verification_required);
    };
    getConfig();
  }, [setIsVerificationRequired]);

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

  if (config.includeConsent) {
    content.push(<ConsentCard key="consentCard" onOpen={onConsentModalOpen} />);
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
          {alert ? (
            <Alert
              status={alert.status}
              minHeight={14}
              maxWidth="5xl"
              zIndex={1}
              position="absolute"
            >
              <AlertIcon />
              <AlertDescription>{alert.description}</AlertDescription>
              <CloseButton
                position="absolute"
                right="8px"
                onClick={() => setAlert(null)}
              />
            </Alert>
          ) : null}
          <Image
            src={config.logo_path}
            height="56px"
            width="304px"
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
          setAlert={setAlert}
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
          setAlert={setAlert}
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
