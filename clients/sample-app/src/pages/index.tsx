import { GetServerSideProps } from "next";
import Head from "next/head";
import { useRouter } from "next/router";
import Script from "next/script";

import Home from "../components/Home";
import pool from "../lib/db";
import { Product } from "../types";

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
      VALID_GTM_REGEX,
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
  const fidesScriptTagUrl = new URL(`${privacyCenterUrl}/fides.js`);
  const router = useRouter();
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { geolocation, property_id } = router.query;

  // If `geolocation=` or `property_id` query params exists, pass those along to the fides.js fetch
  if (geolocation && typeof geolocation === "string") {
    fidesScriptTagUrl.searchParams.append("geolocation", geolocation);
  }
  if (typeof property_id === "string") {
    fidesScriptTagUrl.searchParams.append("property_id", property_id);
  }

  return (
    <>
      <Head>
        <title>Cookie House</title>
      </Head>
      {/**
      Insert the fides.js script and run the GTM integration once ready
      DEFER: using "beforeInteractive" here triggers a lint warning from NextJS
      as it should only be used in the _document.tsx file. This still works and
      ensures that fides.js fires earlier than other scripts, but isn't a best
      practice.
      */}
      {/* eslint-disable-next-line @next/next/no-before-interactive-script-outside-document */}
      <Script
        id="fides-js"
        strategy="beforeInteractive"
        src={fidesScriptTagUrl.href}
        onReady={() => {
          // Enable the GTM integration, if GTM is configured
          if (gtmContainerId) {
            (window as any).Fides.gtm();
          }
        }}
      />
      {/* Insert the GTM script, if a container ID was provided */}
      {gtmContainerId ? (
        <Script id="google-tag-manager" strategy="afterInteractive">
          {`
            (function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
            new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
            j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
            'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
            })(window,document,'script','dataLayer','${gtmContainerId}');
          `}
        </Script>
      ) : null}
      {/* Support for Flutter InAppWebView communication https://inappwebview.dev/docs/webview/javascript/communication */}
      {/* eslint-disable-next-line @next/next/no-before-interactive-script-outside-document */}
      <Script id="flutter-inappwebview" strategy="beforeInteractive">
        {`window.addEventListener("FidesInitialized", function() {
            Fides.onFidesEvent("FidesUpdated", (detail) => {
              window.flutter_inappwebview?.callHandler('FidesUpdated', detail);
            });
          }, {once: true});`}
      </Script>
      <Home privacyCenterUrl={privacyCenterUrl} products={products} />
    </>
  );
};

export default IndexPage;
