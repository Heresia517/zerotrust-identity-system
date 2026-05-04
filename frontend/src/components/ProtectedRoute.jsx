import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children }) {
  const { token, loading } = useAuth();
  if (loading) return <div>Chargement...</div>;
  return token ? children : <Navigate to="/" />;
}