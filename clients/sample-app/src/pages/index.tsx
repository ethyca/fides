/* eslint-disable @next/next/no-sync-scripts */
import { GetServerSideProps } from "next";
import Head from "next/head";
import { useRouter } from "next/router";
import { Product } from "../types";

import Home from "../components/Home";
import pool from "../lib/db";

interface Props {
  products: Product[];
}

export const getServerSideProps: GetServerSideProps<Props> = async () => {
  const results = await pool.query<Product>("SELECT * FROM public.product;");
  return { props: { products: results.rows } };
};

const IndexPage = ({ products }: Props) => {
  // Load the fides.js script from the Fides Privacy Center, assumed to be
  // running at http://localhost:3001
  let fidesScriptTagUrl = "http://localhost:3001/fides.js";
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
        <script src={fidesScriptTagUrl} />
      </Head>

      <Home products={products} />
    </>
  );
};

export default IndexPage;
