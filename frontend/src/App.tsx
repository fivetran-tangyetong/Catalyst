import React, { useState, useEffect } from "react";
import {
  MantineProvider,
  ColorSchemeProvider,
  ColorScheme,
} from "@mantine/core";
import { Notifications } from "@mantine/notifications";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Dashboard } from "./components/Dashboard.tsx";
import { ContentCreator } from "./components/ContentCreator.tsx";

export default function App() {
  const [colorScheme, setColorScheme] = useState<ColorScheme>("light");
  const toggleColorScheme = (value?: ColorScheme) => {
    const next = value || (colorScheme === "dark" ? "light" : "dark");
    setColorScheme(next);
    localStorage.setItem("color-scheme", next);
  };

  useEffect(() => {
    const saved = localStorage.getItem("color-scheme") as ColorScheme | null;
    if (saved) setColorScheme(saved);
  }, []);

  return (
    <ColorSchemeProvider
      colorScheme={colorScheme}
      toggleColorScheme={toggleColorScheme}
    >
      <MantineProvider
        theme={{ colorScheme, primaryColor: "blue", defaultRadius: "md" }}
        withGlobalStyles
        withNormalizeCSS
      >
        <Notifications position="top-right" />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/content/new" element={<ContentCreator />} />
            <Route path="*" element={<Dashboard />} />
          </Routes>
        </BrowserRouter>
      </MantineProvider>
    </ColorSchemeProvider>
  );
}
