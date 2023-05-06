import React from "react";
import Head from "next/head";

// TODO: get styles from store
interface LayoutProps {
    styles?: string;
};

const Layout: React.FC<LayoutProps> = ({ children, styles }) => {
    return (
        <>
            <Head>
                <title>Privacy Center</title>
                <meta name="description" content="Privacy Center" />
                <link rel="icon" href="/favicon.ico" />
                {styles ? <style>{styles}</style> : null}
            </Head>
            {children}
        </>
    );
};

export default Layout;

