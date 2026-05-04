import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="dashboard">
      <header className="header">
        <h1>Tableau de bord</h1>
        <button onClick={handleLogout} className="btn-secondary">Déconnexion</button>
      </header>
      <div className="welcome">
        <p>Bienvenue, {user?.email} !</p>
      </div>
      <div className="actions">
        <Link to="/upload" className="btn-primary">Uploader un fichier</Link>
        <Link to="/files" className="btn-primary">Voir mes fichiers</Link>
      </div>
    </div>
  );
}