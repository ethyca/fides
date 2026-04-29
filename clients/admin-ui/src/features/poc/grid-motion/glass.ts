import { CSSProperties } from "react";

export const GLASS_BG_NEUTRAL = "rgba(126,129,133,0.05)";
export const GLASS_BG_NEUTRAL_HOVER = "rgba(126,129,133,0.08)";

export const GLASS_BG_CRITICAL =
  "linear-gradient(90deg, rgba(255,255,255,0.40), rgba(255,255,255,0.40)), linear-gradient(90deg, rgba(235,182,155,0.32), rgba(235,182,155,0.32))";

export const GLASS_BLUR = "blur(14px)";

export const GLASS_TRANSITION =
  "background-color 0.6s cubic-bezier(0.22,1,0.36,1), box-shadow 0.6s cubic-bezier(0.22,1,0.36,1)";

export const getGlassBgStyle = (
  critical: boolean,
  hovered: boolean,
): CSSProperties => {
  if (critical) {
    return { backgroundImage: GLASS_BG_CRITICAL };
  }
  return {
    backgroundColor: hovered ? GLASS_BG_NEUTRAL_HOVER : GLASS_BG_NEUTRAL,
  };
};

export const buildBoxShadow = (critical: boolean, hovered: boolean): string => {
  if (critical) {
    return hovered
      ? "0 0 22px rgba(225,160,125,0.65), 0 0 52px rgba(225,160,125,0.32), 0 8px 24px rgba(184,112,75,0.18), inset 0 0 48px rgba(252,228,210,0.95)"
      : "0 0 10px rgba(225,160,125,0.40), 0 0 29px rgba(225,160,125,0.16), 0 0 0 rgba(0,0,0,0), inset 0 0 40px rgba(252,228,210,0.65)";
  }
  return hovered
    ? "0 0 20px rgba(126,129,133,0.08), 0 6px 18px rgba(43,46,53,0.04), inset 0 0 24px rgba(255,255,255,0.16)"
    : "0 0 0 rgba(126,129,133,0), 0 0 0 rgba(43,46,53,0), inset 0 0 24px rgba(255,255,255,0.18)";
};
