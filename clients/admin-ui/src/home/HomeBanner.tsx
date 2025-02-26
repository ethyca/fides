import { Flex, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import * as React from "react";

import { useFeatures } from "~/features/common/features";

const HomeBanner = () => {
  const { systemsCount } = useFeatures();
  const hasSystems = systemsCount > 0;

  return (
    <Flex background={palette.FIDESUI_CORINTH}>
      <Flex flexDir="column" maxWidth="600px" padding="10" paddingBottom="16">
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
    </Flex>
  );
};

export default HomeBanner;
