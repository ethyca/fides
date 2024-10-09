// The preview page is used to display a preview of the privacy center in admin UI
// while editing the privacy center experince.
// It is displayed as an iframe in the admin UI, and it receives css overrides using postMessage,
// to display changes made in the admin UI in real-time.

import { useEffect, useState } from "react";

import Home from ".";

const PreviewPage = () => {
  const [stylesheet, setStylesheet] = useState("");

  useEffect(() => {
    window.addEventListener(
      "message",
      (event) => {
        if (event.data.type === "cssOverride") {
          console.log("event.data.css", event.data.css);
          setStylesheet(event.data.css);
        }
      },
      false,
    );
  }, []);

  return (
    <>
      {/* TODO: Safely render style */}
      <style>{stylesheet}</style>
      <Home />
    </>
  );
};
export default PreviewPage;
