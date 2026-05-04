import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { shareFile, getFilePermissions } from '../services/api';

export default function FileShare() {
  const { fileId } = useParams();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [level, setLevel] = useState('READ');
  const [duration, setDuration] = useState('');
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadPermissions = async () => {
      try {
        const { data } = await getFilePermissions(fileId);
        setPermissions(data);
      } catch (err) {
        setError('Erreur chargement permissions');
      } finally {
        setLoading(false);
      }
    };
    loadPermissions();
  }, [fileId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await shareFile(fileId, email, level, duration ? parseInt(duration) : 0);
      // Recharger les permissions
      const { data } = await getFilePermissions(fileId);
      setPermissions(data);
      setEmail('');
      setLevel('READ');
      setDuration('');
    } catch (err) {
      setError('Erreur lors du partage');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div>Chargement...</div>;

  return (
    <div className="file-share">
      <h2>Partager le fichier</h2>
      <button onClick={() => navigate('/files')} className="btn-secondary">
        Retour
      </button>
      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email du destinataire</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="level">Niveau</label>
            <select id="level" value={level} onChange={(e) => setLevel(e.target.value)}>
              <option value="READ">Lecture</option>
              <option value="WRITE">Écriture</option>
              <option value="DELETE">Suppression</option>
              <option value="ADMIN">Admin</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="duration">Durée (secondes, 0 = illimité)</label>
            <input
              id="duration"
              type="number"
              min="0"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
            />
          </div>
          {error && <div className="error">{error}</div>}
          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? 'Partage...' : 'Partager'}
          </button>
        </form>
      </div>
      <h3>Permissions existantes</h3>
      {permissions.length === 0 ? (
        <p>Aucune permission partagée.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Utilisateur</th>
              <th>Niveau</th>
              <th>Expire le</th>
            </tr>
          </thead>
          <tbody>
            {permissions.map((perm) => (
              <tr key={perm.id}>
                <td>{perm.grantee_email || perm.grantee_id}</td>
                <td>{perm.level}</td>
                <td>{perm.expires_at ? new Date(perm.expires_at).toLocaleString() : 'Jamais'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}