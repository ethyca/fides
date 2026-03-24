import React from "react";

export interface ArrowDownRightIconProps extends React.SVGProps<SVGSVGElement> {
  size?: number;
}

const ArrowDownRightIcon = React.forwardRef<
  SVGSVGElement,
  ArrowDownRightIconProps
>(({ size = 16, ...props }, ref) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 16 16"
    fill="none"
    ref={ref}
    {...props}
  >
    <path
      d="M10.781 7.333 7.205 3.757l.943-.943L13.333 8l-5.185 5.185-.943-.943 3.576-3.576H2.667V3.333H4v4z"
      fill="currentColor"
    />
  </svg>
));

export default ArrowDownRightIcon;
