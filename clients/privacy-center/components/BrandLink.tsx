import { EthycaLogo, Link, LinkProps } from "fidesui";

const BrandLink = (props: LinkProps) => (
  <Link fontSize="8px" color="gray.400" isExternal {...props}>
    Powered by <EthycaLogo color="minos.500" />
  </Link>
);

export default BrandLink;
