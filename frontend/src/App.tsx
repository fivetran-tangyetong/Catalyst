import React, { useState, useEffect } from "react";
import {
  MantineProvider,
  ColorSchemeProvider,
  ColorScheme,
  AppShell,
  Loader,
  Center,
} from "@mantine/core";
import { Notifications } from "@mantine/notifications";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useLocation,
} from "react-router-dom";
import { Dashboard } from "./components/Dashboard.tsx";
import { ContentCreator } from "./components/ContentCreator.tsx";
import { MainNavbar } from "./components/MainNavbar.tsx";

// Placeholder components for routes not yet implemented
const PlaceholderComponent = ({ title }: { title: string }) => (
  <div style={{ padding: 20 }}>
    <h2>{title}</h2>
    <p>This page is under development.</p>
  </div>
);

// Auth components
const LoginPage = ({ onLogin }: { onLogin: () => void }) => {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100vh",
      }}
    >
      <h1>Catalyst Marketing Platform</h1>
      <p>AI-powered marketing automation for SMBs</p>
      <button
        onClick={onLogin}
        style={{
          padding: "10px 20px",
          backgroundColor: "#228be6",
          color: "white",
          border: "none",
          borderRadius: "4px",
          cursor: "pointer",
          marginTop: "20px",
        }}
      >
        Login
      </button>
    </div>
  );
};

// Auth context
interface AuthContextType {
  isAuthenticated: boolean;
  login: () => void;
  logout: () => void;
}

const AuthContext = React.createContext<AuthContextType>({
  isAuthenticated: false,
  login: () => {},
  logout: () => {},
});

// Auth provider component
const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already authenticated
    const token = localStorage.getItem("auth_token");
    setIsAuthenticated(!!token);
    setLoading(false);
  }, []);

  const login = () => {
    // In a real app, this would validate credentials and get a token
    localStorage.setItem("auth_token", "demo_token");
    setIsAuthenticated(true);
  };

  const logout = () => {
    localStorage.removeItem("auth_token");
    setIsAuthenticated(false);
  };

  if (loading) {
    return (
      <Center style={{ height: "100vh" }}>
        <Loader size="xl" />
      </Center>
    );
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Protected route component
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = React.useContext(AuthContext);
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

// Main App component
export default function App() {
  const [colorScheme, setColorScheme] = useState<ColorScheme>("light");

  const toggleColorScheme = (value?: ColorScheme) => {
    const nextColorScheme =
      value || (colorScheme === "dark" ? "light" : "dark");
    setColorScheme(nextColorScheme);
    localStorage.setItem("color-scheme", nextColorScheme);
  };

  // Load saved color scheme on mount
  useEffect(() => {
    const savedColorScheme = localStorage.getItem(
      "color-scheme"
    ) as ColorScheme | null;
    if (savedColorScheme) {
      setColorScheme(savedColorScheme);
    }
  }, []);

  return (
    <ColorSchemeProvider
      colorScheme={colorScheme}
      toggleColorScheme={toggleColorScheme}
    >
      <MantineProvider
        theme={{
          colorScheme,
          primaryColor: "blue",
          defaultRadius: "md",
        }}
        withGlobalStyles
        withNormalizeCSS
      >
        <Notifications position="top-right" />
        <BrowserRouter>
          <AuthProvider>
            <Routes>
              {/* <Route path="/login" element={<LoginPage />} /> */}

              {/* Protected routes */}
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />

              <Route
                path="/campaigns"
                element={
                  <ProtectedRoute>
                    <PlaceholderComponent title="Campaigns" />
                  </ProtectedRoute>
                }
              />

              <Route
                path="/campaigns/new"
                element={
                  <ProtectedRoute>
                    <PlaceholderComponent title="Create New Campaign" />
                  </ProtectedRoute>
                }
              />

              <Route
                path="/campaigns/:id"
                element={
                  <ProtectedRoute>
                    <PlaceholderComponent title="Campaign Details" />
                  </ProtectedRoute>
                }
              />

              <Route
                path="/content"
                element={
                  <ProtectedRoute>
                    <PlaceholderComponent title="Content Library" />
                  </ProtectedRoute>
                }
              />

              <Route
                path="/content/new"
                element={
                  <ProtectedRoute>
                    <ContentCreator />
                  </ProtectedRoute>
                }
              />

              <Route
                path="/content/:id"
                element={
                  <ProtectedRoute>
                    <PlaceholderComponent title="Content Details" />
                  </ProtectedRoute>
                }
              />

              <Route
                path="/agents"
                element={
                  <ProtectedRoute>
                    <PlaceholderComponent title="AI Agents" />
                  </ProtectedRoute>
                }
              />

              <Route
                path="/localization"
                element={
                  <ProtectedRoute>
                    <PlaceholderComponent title="Localization" />
                  </ProtectedRoute>
                }
              />

              <Route
                path="/analytics"
                element={
                  <ProtectedRoute>
                    <PlaceholderComponent title="Analytics" />
                  </ProtectedRoute>
                }
              />

              <Route
                path="/scheduler"
                element={
                  <ProtectedRoute>
                    <PlaceholderComponent title="Scheduler" />
                  </ProtectedRoute>
                }
              />

              <Route
                path="/audience"
                element={
                  <ProtectedRoute>
                    <PlaceholderComponent title="Audience" />
                  </ProtectedRoute>
                }
              />

              <Route
                path="/email-outreach"
                element={
                  <ProtectedRoute>
                    <PlaceholderComponent title="Email Outreach" />
                  </ProtectedRoute>
                }
              />

              <Route
                path="/settings"
                element={
                  <ProtectedRoute>
                    <PlaceholderComponent title="Settings" />
                  </ProtectedRoute>
                }
              />

              {/* Fallback route */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AuthProvider>
        </BrowserRouter>
      </MantineProvider>
    </ColorSchemeProvider>
  );
}

// Add auth context to window for login page
const authContextElement = document.createElement("div");
authContextElement.setAttribute("data-auth-context", "true");
document.body.appendChild(authContextElement);

// Expose auth context to login page
(window as any).__exposeAuthContext = (authContext: AuthContextType) => {
  (authContextElement as any).__authContext = authContext;
};
