/* eslint-disable @next/next/no-sync-scripts */
import { GetServerSideProps } from "next";
import Head from "next/head";
import Script from "next/script";
import { useRouter } from "next/router";
import { Product } from "../types";

import Home from "../components/Home";
import pool from "../lib/db";

interface Props {
  gtmContainerId: string | null;
  privacyCenterUrl: string;
  products: Product[];
}

// Regex to ensure the provided GTM container ID appears valid (e.g. "GTM-ABCD123")
// NOTE: this also protects against XSS since this ID is added to a script template
const VALID_GTM_REGEX = /^[0-9a-zA-Z-]+$/;

/**
 * Pass the following server-side ENV variables to the page:
 * - FIDES_SAMPLE_APP__GOOGLE_TAG_MANAGER_CONTAINER_ID: configure a GTM container, e.g. "GTM-ABCD123"
 * - FIDES_SAMPLE_APP__PRIVACY_CENTER_URL: configure Privacy Center URL, e.g. "http://localhost:3001"
 */
export const getServerSideProps: GetServerSideProps<Props> = async () => {
  // Check for a valid FIDES_SAMPLE_APP__GOOGLE_TAG_MANAGER_CONTAINER_ID
  let gtmContainerId = null;
  if (
    process.env.FIDES_SAMPLE_APP__GOOGLE_TAG_MANAGER_CONTAINER_ID?.match(
      VALID_GTM_REGEX
    )
  ) {
    gtmContainerId =
      process.env.FIDES_SAMPLE_APP__GOOGLE_TAG_MANAGER_CONTAINER_ID;
  }

  // Check for a valid FIDES_SAMPLE_APP__PRIVACY_CENTER_URL
  const privacyCenterUrl =
    process.env.FIDES_SAMPLE_APP__PRIVACY_CENTER_URL || "http://localhost:3001";

  // Query the database for the active products
  const results = await pool.query<Product>("SELECT * FROM public.product;");
  const products = results.rows;

  // Pass the server-side props to the page
  return { props: { gtmContainerId, privacyCenterUrl, products } };
};

const IndexPage = ({ gtmContainerId, privacyCenterUrl, products }: Props) => {
  // Load the fides.js script from the Fides Privacy Center, assumed to be
  // running at http://localhost:3001
  let fidesScriptTagUrl = `${privacyCenterUrl}/fides.js`;
  const router = useRouter();
  const { geolocation } = router.query;

  // If a `?geolocation=` query param exists, pass that along to the fides.js fetch
  if (geolocation) {
    fidesScriptTagUrl += `?geolocation=${geolocation}`;
  }

  return (
    <>
      <Head>
        <title>Cookie House</title>
        <meta
          name="description"
          content="Sample Project used within Fides (github.com/ethyca/fides)"
        />
        <link rel="icon" href="/favicon.ico" />
        <link rel="stylesheet" href="https://rsms.me/inter/inter.css" />
        {/* Insert the fides.js script */}
        <script src={fidesScriptTagUrl} />
      </Head>
      {/* Insert the GTM script, if a container ID was provided */}
      <Script id="google-tag-manager" strategy="afterInteractive">
        {`
          (function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
          new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
          j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
          'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
          })(window,document,'script','dataLayer','${gtmContainerId}');
        `}
        {`
          if (window.Fides) {
            window.Fides.gtm();
          }
        `}
      </Script>
      <Home privacyCenterUrl={privacyCenterUrl} products={products} />
    </>
  );
};

export default IndexPage;
