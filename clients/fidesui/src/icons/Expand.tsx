import React from "react";

export interface ExpandIconProps extends React.SVGProps<SVGSVGElement> {
  size?: number;
}

const ExpandIcon = React.forwardRef<SVGSVGElement, ExpandIconProps>(
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
        d="M1 18.1533L3.97559 15.1768L4.68262 15.8838L1.56738 19H5V20H0V15H1V18.1533ZM20 20H15V19H18.293L15.1465 15.8535L15.8535 15.1465L19 18.293V15H20V20ZM5 1H1.70703L4.75293 4.0459L4.0459 4.75293L1 1.70703V5H0V0H5V1ZM20 5H19V1.56738L15.7832 4.7832L15.0762 4.07617L18.1533 1H15V0H20V5Z"
        fill="currentColor"
      />
    </svg>
  ),
);

export default ExpandIcon;
