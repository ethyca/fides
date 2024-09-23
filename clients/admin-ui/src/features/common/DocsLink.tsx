import { Link } from "fidesui";

/**
 * An external link to documentation.
 */
const DocsLink = (props: React.ComponentProps<typeof Link>) => (
  <Link isExternal color="hyperlink_text" {...props} />
);

export default DocsLink;
