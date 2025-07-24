import { Icon, IconProps } from "@chakra-ui/icons";
import React from "react";

type Props = IconProps & { color?: string };

const HorizontalLine = (props: Props) => {
  const { color = "#CBD5E0" } = props;

  return (
    <Icon
      height="2px"
      width="125px"
      viewBox="0 0 125 2"
      {...props}
      color={color}
    >
      <svg
        width="125"
        height="2"
        viewBox="0 0 125 2"
        xmlns="http://www.w3.org/2000/svg"
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
    </Icon>
  );
};

export default HorizontalLine;
