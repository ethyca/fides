import {
  darkAntTheme,
  defaultAntTheme,
  Flex,
  ThemeModeProvider,
  useThemeMode,
} from "fidesui";
import { useFlags } from "~/features/common/features";
import { ConfigProvider } from "antd/lib";
import * as React from "react";
import palette from "fidesui/src/palette/palette.module.scss";

import Layout from "~/features/common/Layout";
import { ThemeModeSegmented } from "~/features/common/ThemeModeToggle";

import HomeBanner from "./HomeBanner";
import HomeContent from "./HomeContent";

const HomeContainerInner = () => {
  const { resolvedMode } = useThemeMode();
  const {
    flags: { alphaDarkMode },
  } = useFlags();

  const activeTheme = resolvedMode === "dark" ? darkAntTheme : defaultAntTheme
  const bgColor = resolvedMode === "dark" ? palette.FIDESUI_BG_MINOS : palette.FIDESUI_FULL_WHITE

  return (
    <ConfigProvider theme={activeTheme}>
      {/* this wrapping div can be removed once global theming is applied */}
      <div
        style={{
          backgroundColor: bgColor,
          minHeight: "100%",
          width: "100%",
        }}
      >
        <Layout title="Home" padded={false}>
          <Flex vertical gap={40} style={{ paddingBottom: 24 }}>
            {/* NOTE: temporary button placement for testing */}
            {alphaDarkMode &&
              <div className="absolute pt-2 pl-2">
                <ThemeModeSegmented />
              </div>
            }

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
    flags: { alphaDarkMode },
  } = useFlags();
  return (
    <ThemeModeProvider defaultMode="light" locked={!alphaDarkMode} scoped wrapperStyle={{ width: "100%" }}>
      <HomeContainerInner />
    </ThemeModeProvider>
  );
}


export default HomeContainer;
