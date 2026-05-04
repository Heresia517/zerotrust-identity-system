import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const uploadFile = (formData) =>
  api.post("/files/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
export const getFiles = () => api.get("/files/");
export const downloadFile = (fileId) =>
  api.get(`/files/${fileId}`, { responseType: "blob" });
export const shareFile = (fileId, granteeEmail, level, duration) =>
  api.post("/permissions/grant", {
    file_id: fileId,
    grantee_email: granteeEmail,
    level,
    duration,
  });
export const getFilePermissions = (fileId) =>
  api.get(`/permissions/file/${fileId}`);

export default api;
