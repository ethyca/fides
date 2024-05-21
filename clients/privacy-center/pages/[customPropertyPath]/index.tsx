/**
 * Renders the custom property path home page.
 * This page catches any route (/something) that hasn't been caught by other pages (home, consent).
 * Properties can have custom paths (/myproperty) so we render the homepage if a property was detected from the path,
 * and we render the 404 page  if we don't have a property that matched the path.
 * @returns The rendered custom property path home page.
 *          If no property matched the path, it renders the 404 page.
 */
import { useProperty } from "~/features/common/property.slice";
import Home from "~/pages";
import Custom404 from "~/pages/404";

const CustomPropertyPathHomePage = () => {
  const property = useProperty();

  if (!property) {
    return <Custom404 />;
  }

  return <Home />;
};

export default CustomPropertyPathHomePage;
