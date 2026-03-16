import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";

import App from "./App";
import { LanguageProvider } from "./i18n/language";
import { queryClient } from "./lib/query-client";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <LanguageProvider>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </LanguageProvider>
  </React.StrictMode>,
);
