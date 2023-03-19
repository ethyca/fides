import { Flex, Text } from "@fidesui/react";
import * as React from "react";

import { useFeatures } from "~/features/common/features";

const HomeBanner: React.FC = () => {
  const { systemsCount } = useFeatures();
  const hasSystems = systemsCount > 0;
  const bannerHeight = "300px";
  const bannerTextWidth = "600px";

  return (
    <Flex
      background="linear-gradient(180deg, #FFFFFF 0%, #F8F8FF 100%);"
      height={bannerHeight}
    >
      {/* Add a scrim that blurs the background so the text is legible at small width */}
      <Flex
        flexShrink={0}
        position="absolute"
        height={bannerHeight}
        width={bannerTextWidth}
        maxWidth="100%"
        backdropFilter="auto"
        backdropBlur="5px"
        sx={{
          // 'mask' property needs to be prefixed in most browsers
          WebkitMask: "linear-gradient(90deg, black 90%, transparent)",
          Mask: "linear-gradient(90deg, black 90%, transparent)",
        }}
      />
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
      <Flex
        flexShrink={0}
        width="100%"
        height={bannerHeight}
        backgroundImage="url('/images/config_splash.svg')"
        backgroundSize="cover"
        backgroundRepeat="no-repeat"
        backgroundPosition="right"
      />
    </Flex>
  );
};

export default HomeBanner;
