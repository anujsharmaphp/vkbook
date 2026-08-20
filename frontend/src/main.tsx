import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider, createBrowserRouter } from "react-router-dom";

import { queryClient } from "./app/queryClient";
import { router } from "./app/router";

import "./design-system/tokens.css";
import "./design-system/base.css";
import "./design-system/components.css";

const appRouter = createBrowserRouter(router);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={appRouter} />
    </QueryClientProvider>
  </StrictMode>,
);
