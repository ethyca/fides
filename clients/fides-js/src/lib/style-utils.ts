type Hsl = {
  h: number;
  s: number;
  l: number;
};

/**
 * Converts hex CSS string to HSL obj.
 * Adapted from https://gist.github.com/xenozauros/f6e185c8de2a04cdfecf
 */
const hexToHSL = (hex: string): Hsl | null => {
  try {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (!result) {
      return null;
    }
    let r = parseInt(result[1], 16);
    let g = parseInt(result[2], 16);
    let b = parseInt(result[3], 16);
    // eslint-disable-next-line @typescript-eslint/no-unused-expressions,no-sequences
    (r /= 255), (g /= 255), (b /= 255);
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    let h;
    let s;
    const l = (max + min) / 2;
    if (max === min) {
      // eslint-disable-next-line no-multi-assign
      h = s = 0; // achromatic
    } else {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      // eslint-disable-next-line default-case
      switch (max) {
        case r:
          h = (g - b) / d + (g < b ? 6 : 0);
          break;
        case g:
          h = (b - r) / d + 2;
          break;
        case b:
          h = (r - g) / d + 4;
          break;
      }
      // @ts-ignore
      h /= 6;
    }
    // @ts-ignore
    return { h, s, l };
  } catch (e) {
    return null;
  }
};

/**
 * Converts an HSL object to a string digestible by CSS
 */
const hslToCssHsl = (hsl: Hsl, valuesOnly = false): string => {
  let cssString = "";
  const h = Math.round(hsl.h * 360);
  const s = Math.round(hsl.s * 100);
  const l = Math.round(hsl.l * 100);

  cssString = `${h},${s}%,${l}%`;
  cssString = !valuesOnly ? `hsl(${cssString})` : cssString;

  return cssString;
};

export enum ColorFormat {
  HEX = "hex",
  HSL = "hsl",
}

/**
 * Given a color, we generate a lighter color, which requires converting to HSL format.
 * Grade 1 is one degree lighter, Grade 2 is two degrees lighter.
 * Default to returning same hex color if there was an issue with conversion to HSL.
 */
export const generateLighterColor = (
  color: string | Hsl,
  format: ColorFormat,
  grade: 1 | 2,
): string => {
  const hsl: Hsl | null =
    format === ColorFormat.HEX ? hexToHSL(color as string) : (color as Hsl);

  if (hsl && hsl.l) {
    // This adds to the lightness parameter in decreasingly smaller increments across pre-determined intervals.
    // The reason for this being that the lighter the original color is, the more impact an increase in lightness
    // has on the resulting color.
    if (hsl.l < 0.25) {
      hsl.l = grade === 1 ? hsl.l + 0.1 : hsl.l + 0.2;
    } else if (hsl.l < 0.5) {
      hsl.l = grade === 1 ? hsl.l + 0.08 : hsl.l + 0.16;
    } else if (hsl.l < 0.75) {
      hsl.l = grade === 1 ? hsl.l + 0.06 : hsl.l + 0.12;
    } else if (hsl.l < 0.9) {
      hsl.l = grade === 1 ? hsl.l + 0.04 : hsl.l + 0.08;
    } else {
      // this is the lightest we can go while ensuring enough contrast with white to be distinguishable
      hsl.l = 0.9;
    }
    return hslToCssHsl(hsl);
  }
  return color as string;
};
