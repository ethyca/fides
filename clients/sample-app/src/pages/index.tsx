/* eslint-disable @next/next/no-sync-scripts */
import { GetServerSideProps } from "next";
import Head from "next/head";
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

const IndexPage = ({ products }: Props) => (
  <>
    <Head>
      <title>Cookie House</title>
      <meta
        name="description"
        content="Sample Project used within Fides (github.com/ethyca/fides)"
      />
      <link rel="icon" href="/favicon.ico" />
      <link rel="stylesheet" href="https://rsms.me/inter/inter.css" />
      <script src="http://localhost:3001/fides.js" />
    </Head>

    <Home products={products} />
  </>
);

export default IndexPage;
