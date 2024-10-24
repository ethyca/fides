import { AntThemeConfig } from "fidesui";

export const antTheme: AntThemeConfig = {
  token: {
    colorPrimary: "#2b2e35",
    colorInfo: "#2b2e35",
    colorSuccess: "#5a9a68",
    colorWarning: "#e59d47",
    colorError: "#d9534f",
    colorLink: "#2272ce",
    colorBgBase: "#ffffff",
    borderRadius: 4,
    wireframe: true,
    colorTextBase: "#2b2e35",
    colorErrorBg: "#ffdcd6",
    colorErrorBorder: "#f2aca5",
    colorWarningBg: "#ffecc9",
    colorWarningBorder: "#ffdba1",
    colorSuccessBorder: "#5a9a68",
    colorPrimaryBg: "#e3e0d9",
    colorBorder: "#e6e6e8",
  },
  components: {
    Button: {
      primaryShadow: "",
      defaultShadow: "",
      dangerShadow: "",
      defaultBg: "#ffffff",
    },
    Layout: {
      bodyBg: "rgb(250,250,250)",
    },
    Alert: {
      colorInfoBg: "rgb(255,255,255)",
      colorInfo: "rgb(147,150,154)",
    },
    Tooltip: {
      colorBgSpotlight: "rgb(43,46,53)",
      colorText: "rgb(250,250,250)",
      colorTextLightSolid: "rgb(250,250,250)",
    },
    Transfer: {
      controlItemBgActiveHover: "rgb(206,202,194)",
    },
    Input: {
      colorBgContainer: "#ffffff",
    },
  },
};
