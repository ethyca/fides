interface SparklineProps {
  points: number[];
  width?: number;
  height?: number;
  stroke?: string;
  fill?: string;
  endDot?: boolean;
}

const Sparkline = ({
  points,
  width = 120,
  height = 36,
  stroke = "#2b2e35",
  fill = "rgba(43,46,53,0.06)",
  endDot = true,
}: SparklineProps) => {
  if (points.length < 2) {
    return null;
  }

  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const padY = 3;
  const innerH = height - padY * 2;
  const stepX = width / (points.length - 1);

  const coords = points.map((value, i) => {
    const x = i * stepX;
    const y = padY + innerH - ((value - min) / range) * innerH;
    return [x, y] as const;
  });

  const linePath = coords
    .map(
      ([x, y], i) => `${i === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`,
    )
    .join(" ");
  const areaPath = `${linePath} L ${width.toFixed(2)} ${height} L 0 ${height} Z`;
  const [endX, endY] = coords[coords.length - 1];

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      style={{ display: "block", overflow: "visible" }}
    >
      <path d={areaPath} fill={fill} />
      <path
        d={linePath}
        fill="none"
        stroke={stroke}
        strokeWidth={1.25}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {endDot && <circle cx={endX} cy={endY} r={2} fill={stroke} />}
    </svg>
  );
};

export default Sparkline;
