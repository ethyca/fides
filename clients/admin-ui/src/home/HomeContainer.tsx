import {
  Alert,
  ConfigProvider,
  darkAntTheme,
  defaultAntTheme,
  Flex,
  Layout as AntLayout,
  ThemeModeProvider,
  useThemeMode,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import dynamic from "next/dynamic";
import * as React from "react";

import { useFlags } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { ThemeModeSegmented } from "~/features/common/ThemeModeToggle";

import HomeContent from "./HomeContent";

const HomeDashboardMockup = dynamic(() => import("./HomeDashboard"), {
  ssr: false,
});

const HomeContainerInner = () => {
  const { resolvedMode } = useThemeMode();
  const {
    flags: { alphaDarkMode, alphaDashboard },
  } = useFlags();

  const activeTheme = resolvedMode === "dark" ? darkAntTheme : defaultAntTheme;
  const bgColor =
    resolvedMode === "dark"
      ? palette.FIDESUI_BG_MINOS
      : palette.FIDESUI_FULL_WHITE;

  if (alphaDashboard) {
    return (
      <ConfigProvider theme={activeTheme}>
        <AntLayout className="h-screen">
          {alphaDarkMode && (
            <AntLayout.Header className="flex items-center justify-end px-10 h-12">
              <ThemeModeSegmented />
            </AntLayout.Header>
          )}
          <AntLayout.Content className="overflow-auto">
            <HomeDashboardMockup />
          </AntLayout.Content>
        </AntLayout>
      </ConfigProvider>
    );
  }

  return (
    <ConfigProvider theme={activeTheme}>
      <div className="min-h-full w-full" style={{ backgroundColor: bgColor }}>
        <Alert
          banner
          type="warning"
          message="BRIEFING · FEB 17, 2026"
          description="Helios scanned 3 systems overnight. 12 fields classified, 4 need review — 2 flagged as biometric in US systems. DSR-4892 SLA deadline tomorrow, pending Marketing."
          showIcon
          primaryAction={{ label: "View actions →", onClick: () => {} }}
          secondaryAction={{ label: "Dismiss", onClick: () => {} }}
        />
        <Layout title="Home" padded={false}>
          <Flex vertical gap={40} className="pb-6">
            {alphaDarkMode && (
              <Flex className="absolute pl-2 pt-2">
                <ThemeModeSegmented />
              </Flex>
            )}
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
