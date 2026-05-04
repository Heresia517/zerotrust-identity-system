import React, { createContext, useState, useContext } from "react";

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [authenticated, setAuthenticated] = useState(
    !!localStorage.getItem("token"),
  );
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);

  const login = async (username, password) => {
    setLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append("client_id", "zt-frontend-client");
      formData.append("grant_type", "password");
      formData.append("username", username);
      formData.append("password", password);
      const response = await fetch(
        "http://localhost:8080/realms/zt-decentralized-iam/protocol/openid-connect/token",
        {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: formData,
        },
      );
      const data = await response.json();
      if (!response.ok)
        throw new Error(data.error_description || "Erreur de connexion");
      localStorage.setItem("token", data.access_token);
      setAuthenticated(true);
      // Optionnel : récupérer les infos utilisateur
      const userInfo = await fetch("http://localhost:8000/auth/me", {
        headers: { Authorization: `Bearer ${data.access_token}` },
      }).then((res) => res.json());
      setUser(userInfo);
      return true;
    } catch (err) {
      console.error(err);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    setAuthenticated(false);
    setUser(null);
    window.location.href = "/";
  };

  return (
    <AuthContext.Provider
      value={{ authenticated, user, loading, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
};
