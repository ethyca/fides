import { NextPage } from "next";

import AboutPage from "./about";

// This page is a copy of the about page, but it will also show the alpha feature flags
const AboutAlpha: NextPage = () => {
  return <AboutPage showAlphaFeatures />;
};
export default AboutAlpha;
