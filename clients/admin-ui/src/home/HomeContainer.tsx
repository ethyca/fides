import {
  ConfigProvider,
  darkAntTheme,
  defaultAntTheme,
  Flex,
  Layout as AntLayout,
  ThemeModeProvider,
  useThemeMode,
} from "fidesui";
import * as React from "react";

import { useFlags } from "~/features/common/features";
import Layout from "~/features/common/Layout";

import HomeBanner from "./HomeBanner";
import HomeContent from "./HomeContent";
import { HomeDashboard } from "./HomeDashboard";

const HomeContainerInner = () => {
  const { resolvedMode } = useThemeMode();
  const {
    flags: { alphaDashboard },
  } = useFlags();

  const activeTheme = resolvedMode === "dark" ? darkAntTheme : defaultAntTheme;
  const bgColor =
    resolvedMode === "dark"
      ? "var(--ant-brand-bg-minos)"
      : "var(--ant-color-white)";

  if (alphaDashboard) {
    return (
      <ConfigProvider theme={activeTheme}>
        <AntLayout className="h-screen">
          <AntLayout.Content className="overflow-auto">
            <HomeDashboard />
          </AntLayout.Content>
        </AntLayout>
      </ConfigProvider>
    );
  }

  return (
    <ConfigProvider theme={activeTheme}>
      <div className="min-h-full w-full" style={{ backgroundColor: bgColor }}>
        <Layout title="Home" padded={false}>
          <Flex vertical gap={40} className="pb-6">
            <HomeBanner />
            <HomeContent />
          </Flex>
        </Layout>
      </div>
    </ConfigProvider>
  );
};

const HomeContainer = () => {
  const {
    flags: { alphaDarkMode, alphaDashboard },
  } = useFlags();
  return (
    <ThemeModeProvider
      defaultMode="light"
      locked={!alphaDarkMode && !alphaDashboard}
      wrapperStyle={{ width: "100%" }}
    >
      <HomeContainerInner />
    </ThemeModeProvider>
  );
};

export default HomeContainer;
