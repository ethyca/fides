import { AntTypography as Typography } from "fidesui";

const { Link } = Typography;
/**
 * An external link to documentation.
 */
const DocsLink = (props: React.ComponentProps<typeof Link>) => (
  <Link target="_blank" rel="noopener noreferrer" {...props} />
);

export default DocsLink;
