import { Box, Flex, Spacer, Text } from "@fidesui/react";
import * as React from "react";

import { useFeatures } from "~/features/common/features";

const HomeBanner: React.FC = () => {
  const { systemsCount } = useFeatures();
  const hasSystems = systemsCount > 0;

  return (
    <Flex
      background="linear-gradient(180deg, #FFFFFF 0%, #F8F8FF 100%);"
      h="300px"
    >
      <Flex
        flexDir="column"
        height="300px"
        width="600px"
        paddingTop="10"
        position="absolute"
        paddingLeft="10"
        paddingRight="10"
      >
        {hasSystems && (
          <>
            <Text
              fontSize="32px"
              fontWeight="semibold"
              h="40px"
              lineHeight="32px"
            >
              Welcome back!
            </Text>
            <Text
              fontSize="18px"
              fontWeight="semibold"
              h="36px"
              lineHeight="28px"
            >
              {`${systemsCount} system${
                systemsCount > 1 ? "s" : ""
              } currently under management`}
            </Text>
            <Text fontSize="14px">
              {`Fides is currently managing privacy for ${systemsCount} system${
                systemsCount > 1 ? "s" : ""
              }. From here you can continue adding and managing systems, process privacy requests or generate reports for your privacy compliance requirements.`}
            </Text>
          </>
        )}
        {!hasSystems && (
          <>
            <Text
              fontSize="32px"
              fontWeight="semibold"
              h="40px"
              lineHeight="32px"
            >
              Welcome to Fides!
            </Text>
            <Text
              fontSize="18px"
              fontWeight="semibold"
              h="36px"
              lineHeight="28px"
            >
              Start your privacy engineering journey today
            </Text>
            <Text fontSize="14px">
              Step one in setting up your privacy engineering platform is adding
              the systems you need to manage. Use the links below to add and
              configure systems within Fides for data mapping and privacy
              request automation.
            </Text>
          </>
        )}
      </Flex>
      <Spacer />
      <Flex
        flexShrink={0}
        width="100%"
        height="300px"
        backgroundImage="url('/images/config_splash.svg')"
        backgroundSize="cover"
        backgroundRepeat="no-repeat"
        backgroundPosition="right"
      />
    </Flex>
  );
};

export default HomeBanner;
