import { useEffect, useRef } from "react";

interface PrivacyCenterPreviewProps {
  stylesheet?: string;
}

const PrivacyCenterPreview = ({ stylesheet }) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    setTimeout(() => {
      iframeRef.current?.contentWindow?.postMessage(
        { type: "alert", message: "Hello! This is a message from Admin-UI!" },
        "*",
      );
    }, 5000);
  }, []);

  return (
    <div className="size-full">
      <iframe
        className="size-full"
        src="http://localhost:3001/"
        title="Privacy Center"
        ref={iframeRef}
      />
    </div>
  );
};
export default PrivacyCenterPreview;
