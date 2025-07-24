import { NextPage } from "next";

import AboutPage from "./index";

// This page is a copy of the about page, but it will also show the alpha feature flags
const AboutAlpha: NextPage = () => {
  return <AboutPage showAlphaFeatures />;
};
export default AboutAlpha;
