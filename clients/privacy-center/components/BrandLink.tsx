import { EthycaLogo, Link, LinkProps } from "fidesui";

const BrandLink = (props: LinkProps) => (
  <Link
    fontSize="8px"
    color="gray.400"
    isExternal
    textDecoration="none"
    _hover={{ textDecoration: "none" }}
    {...props}
  >
    Powered by <EthycaLogo color="minos.500" h="20px" w="31px" />
  </Link>
);

export default BrandLink;
