import { antTheme } from "fidesui";

export const getTrendPrefix = (trend: number) => {
  if (trend < 0) {
    return "-";
  }
  if (trend > 0) {
    return "+";
  }
  return "";
};

export const getTrendColor = (
  trend: number,
  token: ReturnType<typeof antTheme.useToken>["token"],
) => {
  if (trend < 0) {
    return token.colorSuccess;
  }
  if (trend > 0) {
    return token.colorError;
  }
  return token.colorTextSecondary;
};
