import { AntButton, forwardRef } from "fidesui";

/**
 * Provides the default styling props for buttons used by Privacy Request actions.
 */
export const StyledButton = forwardRef((props, ref) => (
  <AntButton ref={ref} size="small" {...props} />
));

export default StyledButton;
