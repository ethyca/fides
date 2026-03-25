import React from "react";

export interface ManualSetupIconProps extends React.SVGProps<SVGSVGElement> {
  size?: number;
}

const ManualSetupIcon = React.forwardRef<SVGSVGElement, ManualSetupIconProps>(
  ({ size = 16, ...props }, ref) => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 21"
      fill="none"
      ref={ref}
      {...props}
    >
      <path
        d="M 6.2164592,20.0346 0.57734916,10.2673 6.2164592,0.5 H 17.494859 l 5.6391,9.7673 -5.6391,9.7673 z"
        stroke="currentColor"
        strokeWidth="1.25"
      />
      <path
        d="m 8.0165592,16.9212 -3.83911,-6.6496 3.83911,-6.6496 h 7.6783998 l 3.8391,6.6496 -3.8391,6.6496 z"
        stroke="currentColor"
        strokeWidth="1.25"
      />
      <path
        d="m 9.8166592,13.7961 -2.0391,-3.5319 2.0391,-3.5319 h 4.0782998 l 2.0392,3.5319 -2.0392,3.5319 z"
        stroke="currentColor"
        strokeWidth="1.25"
      />
    </svg>
  ),
);

ManualSetupIcon.displayName = "ManualSetupIcon";

export default ManualSetupIcon;
