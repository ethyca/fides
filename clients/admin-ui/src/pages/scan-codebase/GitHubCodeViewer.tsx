import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { materialLight } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface GitHubCodeViewerProps {
  url: string;
  language: string;
}

const GitHubCodeViewer: React.FC<GitHubCodeViewerProps> = ({ url, language }) => {
  const [code, setCode] = useState<string | null>(null);

  useEffect(() => {
    async function fetchGitHubCode() {
      try {
        const response = await axios.get(url);
        const codeLines = response.data.split('\n');

        // Extract line numbers from the URL
        const matches = url.match(/#L(\d+)-L(\d+)/);
        if (matches) {
          const startLine = Number(matches[1]);
          const endLine = Number(matches[2]);

          if (!isNaN(startLine) && !isNaN(endLine)) {
            const selectedCode = codeLines.slice(startLine - 1, endLine).join('\n');
            setCode(selectedCode);
            return;
          }
        }

        // If no line numbers are specified, display the entire code
        setCode(response.data);
      } catch (error) {
        console.error('Error fetching GitHub code:', error);
      }
    }

    fetchGitHubCode();
  }, [url]);

  if (!code) {
    return <div>Loading...</div>;
  }

  return (
    <SyntaxHighlighter language={language} style={materialLight}>
      {code}
    </SyntaxHighlighter>
  );
};

export default GitHubCodeViewer;
