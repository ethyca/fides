import Sparkline from "./Sparkline";

const INK = "#2b2e35";
const INK_MUTED = "rgba(43,46,53,0.55)";
const ACCENT_WARM = "#C97B3D";
const ACCENT_CRITICAL = "#B85A2E";
const STROKE_FAINT = "rgba(43,46,53,0.10)";

const MONO_FONT =
  "'Basier Square Mono', ui-monospace, SFMono-Regular, monospace";

export type Tone = "neutral" | "warn" | "critical";

const toneColor = (tone?: Tone) => {
  if (tone === "critical") {
    return ACCENT_CRITICAL;
  }
  if (tone === "warn") {
    return ACCENT_WARM;
  }
  return INK;
};

interface BlockProps {
  label: string;
  caption: string;
  captionTone?: Tone;
  children: JSX.Element;
}

const Block = ({ label, caption, captionTone, children }: BlockProps) => (
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      gap: 6,
      flex: 1,
      minWidth: 0,
    }}
  >
    {children}
    <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
      <span
        style={{
          fontFamily: MONO_FONT,
          fontSize: 13,
          fontWeight: 500,
          color: toneColor(captionTone),
          letterSpacing: "-0.01em",
        }}
      >
        {caption}
      </span>
      <span
        style={{
          fontSize: 9,
          letterSpacing: "0.10em",
          textTransform: "uppercase",
          color: INK_MUTED,
        }}
      >
        {label}
      </span>
    </div>
  </div>
);

interface HBarProps {
  fraction: number;
  width?: number;
  height?: number;
  tone?: Tone;
}

export const HBar = ({
  fraction,
  width = 120,
  height = 6,
  tone = "neutral",
}: HBarProps) => (
  <svg
    width="100%"
    height={height}
    viewBox={`0 0 ${width} ${height}`}
    preserveAspectRatio="none"
  >
    <rect width={width} height={height} fill={STROKE_FAINT} rx={1} />
    <rect
      width={Math.max(2, width * Math.min(1, Math.max(0, fraction)))}
      height={height}
      fill={toneColor(tone)}
      rx={1}
    />
  </svg>
);

interface DotRowProps {
  filled: number;
  total?: number;
  tone?: Tone;
  size?: number;
}

export const DotRow = ({
  filled,
  total = 12,
  tone = "neutral",
  size = 6,
}: DotRowProps) => (
  <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
    {Array.from({ length: total }).map((_, i) => {
      const isFilled = i < filled;
      return (
        <span
          // eslint-disable-next-line react/no-array-index-key
          key={i}
          style={{
            width: size,
            height: size,
            borderRadius: 1,
            background: isFilled ? toneColor(tone) : STROKE_FAINT,
            display: "block",
          }}
        />
      );
    })}
  </div>
);

interface MiniSparkProps {
  points: number[];
  tone?: Tone;
}

const FILL_BY_TONE: Record<Tone, string> = {
  neutral: "rgba(43,46,53,0.06)",
  warn: "rgba(201,123,61,0.10)",
  critical: "rgba(184,90,46,0.10)",
};

export const MiniSpark = ({ points, tone = "neutral" }: MiniSparkProps) => (
  <Sparkline
    points={points}
    width={140}
    height={28}
    stroke={toneColor(tone)}
    fill={FILL_BY_TONE[tone]}
    endDot
  />
);

export interface VizBlockProps {
  kind: "hbar" | "spark" | "dots";
  label: string;
  caption: string;
  captionTone?: Tone;
  fraction?: number;
  points?: number[];
  filled?: number;
  total?: number;
  tone?: Tone;
}

export const VizBlock = ({
  kind,
  label,
  caption,
  captionTone,
  fraction = 0,
  points = [],
  filled = 0,
  total = 12,
  tone = "neutral",
}: VizBlockProps) => {
  let viz: JSX.Element;
  if (kind === "hbar") {
    viz = <HBar fraction={fraction} tone={tone} />;
  } else if (kind === "spark") {
    viz = <MiniSpark points={points} tone={tone} />;
  } else {
    viz = <DotRow filled={filled} total={total} tone={tone} />;
  }
  return (
    <Block label={label} caption={caption} captionTone={captionTone}>
      {viz}
    </Block>
  );
};
