import { EthycaLogo, Link, LinkProps } from "fidesui";

const BrandLink = (props: LinkProps) => (
  <Link
    fontSize="8px"
    color="gray.400"
    href="https://ethyca.com"
    isExternal
    {...props}
  >
    Powered by <EthycaLogo color="minos.500" />
  </Link>
);

export default BrandLink;
