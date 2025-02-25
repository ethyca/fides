"use server";

// import "swagger-ui-react/swagger-ui.css";

import { NextPage } from "next";
import { notFound } from "next/navigation";
// import SwaggerUI from "swagger-ui-react";

const DocsPage: NextPage = () => {
  const isDevelopmentBuild = process.env.NODE_ENV === "development";
  if (!isDevelopmentBuild) {
    return notFound();
  }

  //
  return <h1>Not available</h1>;
  // return <SwaggerUI url="/api/openapi.json" />;
};
export default DocsPage;
