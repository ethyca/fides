type Hsl = {
  h: number;
  s: number;
  l: number;
};

// adapted from https://gist.github.com/xenozauros/f6e185c8de2a04cdfecf
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

// converts hsl raw object to a string digestible by CSS
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

// takes color, lightens it by grade, returns HSL string or same hex color in case of error
// grade 1 is one degree lighter, grade 2 is two degrees lighter
export const generateLighterColor = (
  color: string | Hsl,
  format: ColorFormat,
  grade: 1 | 2
): string => {
  const hsl: Hsl | null =
    format === ColorFormat.HEX ? hexToHSL(color as string) : (color as Hsl);

  if (hsl) {
    if (hsl.l < 0.25) {
      // this is the lowest we can go ensuring enough contrast with the original color
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
