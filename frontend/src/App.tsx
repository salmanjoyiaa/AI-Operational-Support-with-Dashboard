import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Analytics } from "./pages/Analytics";
import { Dashboard } from "./pages/Dashboard";
import { KnowledgeBase } from "./pages/KnowledgeBase";
import { Settings } from "./pages/Settings";
import { TicketDetail } from "./pages/TicketDetail";
import { TicketInbox } from "./pages/TicketInbox";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="/tickets" element={<TicketInbox />} />
        <Route path="/tickets/:id" element={<TicketDetail />} />
        <Route path="/knowledge-base" element={<KnowledgeBase />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}
