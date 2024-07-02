import { Flex, Text } from "fidesui";
import * as React from "react";

import { useFeatures } from "~/features/common/features";

const HomeBanner = () => {
  const { systemsCount } = useFeatures();
  const hasSystems = systemsCount > 0;
  const bannerHeight = "300px";
  const bannerTextWidth = "600px";

  return (
    <Flex
      position="relative"
      height={bannerHeight}
      background="linear-gradient(180deg, #FFFFFF 0%, #F8F8FF 100%);"
      overflow="hidden"
    >
      <Flex
        flexDir="column"
        position="absolute"
        height={bannerHeight}
        width={bannerTextWidth}
        maxWidth="100%"
        padding="10"
      >
        {hasSystems && (
          <>
            <Text fontSize="3xl" fontWeight="semibold">
              Welcome back!
            </Text>
            <Text marginTop="1" fontSize="lg" fontWeight="semibold">
              {`${systemsCount} system${
                systemsCount > 1 ? "s" : ""
              } currently under management`}
            </Text>
            <Text marginTop="1" fontSize="sm">
              {`Fides is currently managing privacy for ${systemsCount} system${
                systemsCount > 1 ? "s" : ""
              }. From here you can continue adding and managing systems, process privacy requests or generate reports for your privacy compliance requirements.`}
            </Text>
          </>
        )}
        {!hasSystems && (
          <>
            <Text fontSize="3xl" fontWeight="semibold">
              Welcome to Fides!
            </Text>
            <Text marginTop="1" fontSize="lg" fontWeight="semibold">
              Start your privacy engineering journey today
            </Text>
            <Text marginTop="1" fontSize="sm">
              Step one in setting up your privacy engineering platform is adding
              the systems you need to manage. Use the links below to add and
              configure systems within Fides for data mapping and privacy
              request automation.
            </Text>
          </>
        )}
      </Flex>
      {/* Render the background image, using a min-width here to ensure there is
      enough left margin to avoid colliding with the banner text above */}
      <Flex
        flexShrink={0}
        width="100%"
        minWidth="1120px"
        height={bannerHeight}
        backgroundImage="url('/images/config_splash.svg')"
        backgroundSize="contain"
        backgroundRepeat="no-repeat"
        backgroundPosition="right"
      />
    </Flex>
  );
};

export default HomeBanner;
