import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ClusterProvider } from "./lib/cluster-context";
import { OverviewPage } from "./pages/Overview";
import { DiscoveryPage } from "./pages/Discovery";
import { TopologyPage } from "./pages/Topology";
import { JobsPage } from "./pages/Jobs";
import { TasksPage } from "./pages/Tasks";
import { ResultsPage } from "./pages/Results";
import { PerformancePage } from "./pages/Performance";
import { ExperimentsPage } from "./pages/Experiments";
import { SettingsPage } from "./pages/Settings";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { refetchOnWindowFocus: false, staleTime: 5_000 },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ClusterProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<AppShell />}>
              <Route index element={<OverviewPage />} />
              <Route path="discovery" element={<DiscoveryPage />} />
              <Route path="topology" element={<TopologyPage />} />
              <Route path="jobs" element={<JobsPage />} />
              <Route path="tasks" element={<TasksPage />} />
              <Route path="results" element={<ResultsPage />} />
              <Route path="performance" element={<PerformancePage />} />
              <Route path="experiments" element={<ExperimentsPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ClusterProvider>
    </QueryClientProvider>
  );
}
