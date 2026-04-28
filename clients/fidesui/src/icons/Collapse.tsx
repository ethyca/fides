import React from "react";

export interface CollapseIconProps extends React.SVGProps<SVGSVGElement> {
  size?: number;
}

const CollapseIcon = React.forwardRef<SVGSVGElement, CollapseIconProps>(
  ({ size = 20, ...props }, ref) => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 20 20"
      fill="none"
      ref={ref}
      {...props}
    >
      <path
        d="M5 20H4V16H0V15H5V20ZM20 16H16V20H15V15H20V16ZM16 4H20V5H15V0H16V4ZM5 5H0V4H4V0H5V5Z"
        fill="currentColor"
      />
    </svg>
  ),
);

export default CollapseIcon;
