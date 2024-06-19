import { useProperty } from "~/features/common/property.slice";
import Custom404 from "~/pages/404";
import Consent from "~/pages/consent";

/**
 * Renders the consent page for a custom property path.
 * If the property is not found, renders a 404 page.
 */
const CustomPropertyPathConsentPage = () => {
  const property = useProperty();

  if (!property) {
    return <Custom404 />;
  }

  return <Consent />;
};

export default CustomPropertyPathConsentPage;
