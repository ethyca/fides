import React from "react";

/**
 * React 19-compatible replacement for @chakra-ui/icons createIcon.
 *
 * Chakra UI v2's createIcon uses React.Children.toArray internally in a way
 * that is incompatible with React 19's stricter child validation. This shim
 * provides the same API but renders a simple SVG component directly.
 */
export const createIcon = ({
  displayName,
  viewBox = "0 0 24 24",
  path,
  d,
}: {
  displayName: string;
  viewBox?: string;
  path?: React.ReactElement;
  d?: string;
  defaultProps?: Record<string, unknown>;
}) => {
  const IconComponent = React.forwardRef<
    SVGSVGElement,
    React.SVGProps<SVGSVGElement>
  >((props, ref) => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox={viewBox}
      fill="currentColor"
      width="1em"
      height="1em"
      ref={ref}
      {...props}
    >
      {path ?? (d ? <path d={d} fill="currentColor" /> : null)}
    </svg>
  ));

  IconComponent.displayName = displayName;
  return IconComponent;
};
