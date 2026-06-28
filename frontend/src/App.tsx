import { Routes, Route } from "react-router-dom";
import { UserProvider } from "./context/UserContext";
import Layout from "./components/Layout";
import LobbyPage from "./pages/LobbyPage";
import ProblemPage from "./pages/ProblemPage";
import AdminPage from "./pages/AdminPage";

export default function App() {
  return (
    <UserProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<LobbyPage />} />
          <Route path="/problem/:slug" element={<ProblemPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="*" element={<LobbyPage />} />
        </Route>
      </Routes>
    </UserProvider>
  );
}
