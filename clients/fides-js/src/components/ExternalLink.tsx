import { ComponentChildren, h } from "preact";

const ExternalLink = ({
  href,
  children,
}: {
  href: string;
  children: ComponentChildren;
}) => (
  <a
    href={href}
    className="fides-external-link"
    target="_blank"
    rel="noopener noreferrer"
  >
    {children}
  </a>
);

export default ExternalLink;
