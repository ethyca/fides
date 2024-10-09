import { useEffect, useRef } from "react";

interface PrivacyCenterPreviewProps {
  stylesheet?: string;
}

const PrivacyCenterPreview = ({ stylesheet }: PrivacyCenterPreviewProps) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const sendCssOverrideMessageToIframe = (css?: string) => {
    if (css) {
      iframeRef.current?.contentWindow?.postMessage(
        { type: "cssOverride", css },
        "*",
      );
    }
  };

  // Send the css override message to the iframe after 5 seconds
  // TODO: Implement a better way to check for when iframe is ready
  // (maybe send a message from the iframe to the parent window?)
  useEffect(() => {
    setTimeout(() => {
      sendCssOverrideMessageToIframe(stylesheet);
    }, 5000);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Send the css override message to the iframe whenever the stylesheet changes
  useEffect(() => {
    sendCssOverrideMessageToIframe(stylesheet);
  }, [stylesheet]);

  return (
    <>
      <style jsx>{`
        ${stylesheet}
      `}</style>
      <div className="size-full">
        <iframe
          className="size-full"
          // TODO: get the iframe src for the privacy center from the environment/configs
          src="http://localhost:3001/preview"
          title="Privacy Center Preview"
          ref={iframeRef}
        />
      </div>
    </>
  );
};
export default PrivacyCenterPreview;
