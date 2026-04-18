import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppShell } from "./ui/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { ReportDetailPage } from "./pages/ReportDetailPage";
import { ReportsPage } from "./pages/ReportsPage";
import { SourcesPage } from "./pages/SourcesPage";
import { WorkflowRunsPage } from "./pages/WorkflowRunsPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "sources", element: <SourcesPage /> },
      { path: "documents", element: <DocumentsPage /> },
      { path: "reports", element: <ReportsPage /> },
      { path: "reports/:reportId", element: <ReportDetailPage /> },
      { path: "workflow-runs", element: <WorkflowRunsPage /> }
    ]
  }
]);
