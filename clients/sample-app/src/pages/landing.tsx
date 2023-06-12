import Head from "next/head";

import Landing from "../components/Landing";

const LandingPage = () => (
  <>
    <Head>
      <title>Welcome to Fides</title>
      <link rel="icon" href="/favicon.ico" />
      <meta charSet="utf-8" />
      {/* eslint-disable-next-line @next/next/google-font-display, @next/next/no-page-custom-font */}
      <link
        rel="stylesheet"
        href="https://fonts.googleapis.com/css?family=Source+Sans+Pro:300,400,500,600,700"
      />
    </Head>
    <Landing />
  </>
);

export default LandingPage;
