// Module augmentation for our custom palette tokens. With these declared as
// part of AliasToken, ConfigProvider's `theme.token` accepts them without
// excess-property errors and `useToken()` returns them with proper types.

declare module "antd/es/theme/interface/alias" {
  interface AliasToken {
    // Brand palette
    brandMinos: string;
    brandBgMinos: string;
    brandCorinth: string;
    brandBgCorinth: string;
    brandLimestone: string;
    brandTerracotta: string;
    brandBgTerracotta: string;
    brandOlive: string;
    brandBgOlive: string;
    brandMarble: string;
    brandBgMarble: string;
    brandSandstone: string;
    brandBgSandstone: string;
    brandNectar: string;
    brandBgNectar: string;
    brandAlert: string;
    brandBgAlert: string;
    brandBgCaution: string;
    brandBgError: string;
    brandBgWarning: string;
    brandBgSuccess: string;
    brandBgInfo: string;
    brandErrorText: string;
    brandSuccessText: string;

    // Neutral scale
    neutral50: string;
    neutral75: string;
    neutral100: string;
    neutral200: string;
    neutral300: string;
    neutral400: string;
    neutral500: string;
    neutral600: string;
    neutral700: string;
    neutral800: string;
    neutral900: string;
  }
}

export {};
