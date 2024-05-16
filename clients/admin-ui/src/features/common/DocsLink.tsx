import { Link } from "fidesui";

/**
 * An external link to documentation.
 */
const DocsLink = (props: React.ComponentProps<typeof Link>) => (
  <Link isExternal color="complimentary.500" {...props} />
);

export default DocsLink;
