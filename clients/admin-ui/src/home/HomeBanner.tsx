import {
  Flex, Text, Title, useThemeMode
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import * as React from "react";

import { useFeatures } from "~/features/common/features";

const HomeBanner = () => {
  const { systemsCount } = useFeatures();
  const { resolvedMode } = useThemeMode();

  // Read the background color directly from the theme config so it always
  // matches the applied theme regardless of how Ant resolves CSS variables.
  // Once we're using ant Layout globally, we won't need to hard-code the colors.
  const bgColor = resolvedMode === "dark" ? palette.FIDESUI_BG_MINOS : palette.FIDESUI_CORINTH

  const hasSystems = systemsCount > 0;

  return (
    <Flex style={{ background: bgColor }}>
      <Flex
        vertical
        style={{ maxWidth: 600, padding: 40, paddingBottom: 64 }}
      >
        {hasSystems && (
          <>
            <Title level={3} style={{ margin: 0 }}>
              Welcome back!
            </Title>
            <Text
              strong
              style={{ fontSize: "1.125rem", display: "block", marginTop: 4 }}
            >
              {`${systemsCount} system${systemsCount > 1 ? "s" : ""
                } currently under management`}
            </Text>
            <Text style={{ fontSize: "0.875rem", display: "block", marginTop: 4 }}>
              {`Fides is currently managing privacy for ${systemsCount} system${systemsCount > 1 ? "s" : ""
                }. From here you can continue adding and managing systems, process privacy requests or generate reports for your privacy compliance requirements.`}
            </Text>
          </>
        )}
        {!hasSystems && (
          <>
            <Title level={3} style={{ margin: 0 }}>
              Welcome to Fides!
            </Title>
            <Text
              strong
              style={{ fontSize: "1.125rem", display: "block", marginTop: 4 }}
            >
              Start your privacy engineering journey today
            </Text>
            <Text style={{ fontSize: "0.875rem", display: "block", marginTop: 4 }}>
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
