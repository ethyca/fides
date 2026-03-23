import React from "react";

type Props = React.SVGProps<SVGSVGElement> & { color?: string };

const HorizontalLine = (props: Props) => {
  const { color = "#CBD5E0", ...rest } = props;

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      height="2px"
      width="125px"
      viewBox="0 0 125 2"
      {...rest}
    >
      <line
        x1="0.28418"
        y1="1"
        x2="124.558"
        y2="1"
        stroke={color}
        strokeWidth="2"
      />
    </svg>
  );
};

export default HorizontalLine;
