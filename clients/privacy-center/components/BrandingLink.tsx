import { EthycaLogo, Link } from "fidesui";

const BrandingLink = () => (
  <Link
    position="absolute"
    right={6}
    fontSize="8px"
    color="gray.400"
    href="https://ethyca.com"
    isExternal
  >
    Powered by <EthycaLogo color="minos.500" />
  </Link>
);

export default BrandingLink;
