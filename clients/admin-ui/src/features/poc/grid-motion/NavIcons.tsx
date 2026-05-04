import type { CSSProperties } from "react";

type IconProps = {
  size?: number;
  style?: CSSProperties;
};

export const FidesIcon = ({ size = 20, style }: IconProps) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 20 20"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={style}
  >
    <rect width="20" height="20" fill="currentColor" />
  </svg>
);

export const AstralisIcon = ({ size = 24, style }: IconProps) => (
  <svg
    width={size}
    height={size * (44 / 48)}
    viewBox="0 0 48 44"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={style}
  >
    <path
      d="M15.0977 20.7774V23.2216H13V20.7774H15.0977ZM32.9023 20.7774V23.2216H35V20.7774H32.9023ZM29.9158 23.7111C29.2679 26.3753 26.86 28.3575 24 28.3575C21.14 28.3575 18.7321 26.3753 18.0842 23.7111H15.5861C16.2758 27.7327 19.7859 30.8028 24 30.8028C28.2141 30.8028 31.7242 27.7327 32.4139 23.7111H29.9158ZM24 13.1973C19.7859 13.1973 16.2758 16.2652 15.5861 20.289H18.0842C18.7321 17.6248 21.14 15.6426 24 15.6426C26.86 15.6426 29.2679 17.6248 29.9158 20.289H32.4139C31.7242 16.2652 28.2141 13.1973 24 13.1973ZM18.5682 20.7774V23.2216H29.4285V20.7774H18.5682Z"
      fill="currentColor"
    />
  </svg>
);

export const HeliosIcon = ({ size = 24, style }: IconProps) => (
  <svg
    width={size}
    height={size * (44 / 48)}
    viewBox="0 0 48 44"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={style}
  >
    <path
      d="M13 28.111H22.2884V30.5552H13V28.111ZM25.7116 28.111V30.5552H35V28.111H25.7116ZM13 19.9226L22.2884 27.6248V24.4491L13 16.7469V19.9226ZM25.7116 24.4491V27.6248L35 19.9248V16.7491L25.7116 24.4491ZM22.7779 13.4447V23.9563H25.2221V13.4447H22.7779Z"
      fill="currentColor"
    />
  </svg>
);

export const JanusIcon = ({ size = 24, style }: IconProps) => (
  <svg
    width={size}
    height={size * (44 / 48)}
    viewBox="0 0 48 44"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={style}
  >
    <path
      d="M31.7398 23.711H34.9989L28.9679 30.5548H25.7066L31.7398 23.711ZM34.9989 20.289L31.9823 16.8671L28.9657 13.4452H25.7099V13.4474L31.7409 20.289H35H34.9989ZM22.2868 13.4496L22.2923 13.4452H19.0332L13 20.289H16.2591L22.2868 13.4496ZM13 23.711L19.031 30.5548H22.2923L16.2591 23.711H13ZM16.7475 20.7785V23.2226H22.2868V20.7785H16.7475ZM25.7099 20.7785V23.2226H31.2514V20.7785H25.7099Z"
      fill="currentColor"
    />
  </svg>
);

export const LetheIcon = ({ size = 24, style }: IconProps) => (
  <svg
    width={size}
    height={size * (44 / 48)}
    viewBox="0 0 48 44"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={style}
  >
    <path
      d="M16.7884 28.1105L22.2884 22.0627V25.6971L17.8708 30.5547H13V28.1105H16.7884ZM30.1281 13.4442L25.7105 18.3018V21.934L31.2083 15.8884H35V13.4442H30.1281ZM22.3478 13.4442L22.2895 13.508L16.7895 19.5558H13V22H17.8719L22.2895 17.1424L25.6522 13.4442H22.3478ZM30.1281 22L25.7105 26.8576L22.3467 30.5558H25.6511L25.7094 30.4898L31.2072 24.4442H34.9989V22H30.127H30.1281Z"
      fill="currentColor"
    />
  </svg>
);

export const LightningIcon = ({ size = 22, style }: IconProps) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={style}
  >
    <path d="M13.5 2L4 14h6l-1.5 8L18 10h-6l1.5-8z" fill="currentColor" />
  </svg>
);

export const GearIcon = ({ size = 22, style }: IconProps) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={style}
  >
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M12 8.5a3.5 3.5 0 100 7 3.5 3.5 0 000-7zm-2 3.5a2 2 0 114 0 2 2 0 01-4 0z"
      fill="currentColor"
    />
    <path
      d="M10.3 2.4a1 1 0 011-.9h1.4a1 1 0 011 .9l.2 1.5a7.5 7.5 0 011.7 1l1.4-.5a1 1 0 011.2.4l.7 1.2a1 1 0 01-.2 1.3l-1.1 1a7.5 7.5 0 010 2l1.1 1a1 1 0 01.2 1.3l-.7 1.2a1 1 0 01-1.2.4l-1.4-.5a7.5 7.5 0 01-1.7 1l-.2 1.5a1 1 0 01-1 .9h-1.4a1 1 0 01-1-.9l-.2-1.5a7.5 7.5 0 01-1.7-1l-1.4.5a1 1 0 01-1.2-.4l-.7-1.2a1 1 0 01.2-1.3l1.1-1a7.5 7.5 0 010-2l-1.1-1a1 1 0 01-.2-1.3l.7-1.2a1 1 0 011.2-.4l1.4.5a7.5 7.5 0 011.7-1l.2-1.5zm1.4.6l-.2 1.6a1 1 0 01-.6.8 5.5 5.5 0 00-1.7 1 1 1 0 01-1 .2l-1.5-.5-.4.7 1.2 1a1 1 0 01.3 1 5.5 5.5 0 000 2 1 1 0 01-.3 1l-1.2 1 .4.7 1.5-.5a1 1 0 011 .2 5.5 5.5 0 001.7 1 1 1 0 01.6.8l.2 1.6h.6l.2-1.6a1 1 0 01.6-.8 5.5 5.5 0 001.7-1 1 1 0 011-.2l1.5.5.4-.7-1.2-1a1 1 0 01-.3-1 5.5 5.5 0 000-2 1 1 0 01.3-1l1.2-1-.4-.7-1.5.5a1 1 0 01-1-.2 5.5 5.5 0 00-1.7-1 1 1 0 01-.6-.8l-.2-1.6h-.6z"
      fill="currentColor"
    />
  </svg>
);
