import {
  ConfigProvider,
  darkAntTheme,
  defaultAntTheme,
  Flex,
  ThemeModeProvider,
  useThemeMode,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import * as React from "react";

import { useFlags } from "~/features/common/features";
import Layout from "~/features/common/Layout";

import { CommandBar } from "./CommandBar";
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
      ? palette.FIDESUI_BG_MINOS
      : palette.FIDESUI_FULL_WHITE;

  if (alphaDashboard) {
    return (
      <ConfigProvider theme={activeTheme}>
        <div className="flex h-screen flex-col">
          <CommandBar />
          <div className="flex-1 overflow-auto">
            <HomeDashboard />
          </div>
        </div>
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
