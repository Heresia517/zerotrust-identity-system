import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getFiles, downloadFile } from '../services/api';
import * as crypto from '../services/crypto';

export default function FileList() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      const { data } = await getFiles();
      setFiles(data);
    } catch (err) {
      setError('Erreur lors du chargement des fichiers');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (fileId, fileName) => {
    setDownloading(true);
    try {
      const response = await downloadFile(fileId);
      const blob = response.data;
      // Lire le blob comme ArrayBuffer
      const buffer = await blob.arrayBuffer();
      // Extraire IV (12 premiers bytes) et données chiffrées
      const iv = new Uint8Array(buffer.slice(0, 12));
      const encryptedData = buffer.slice(12);

      // Récupérer la clé depuis localStorage (base64)
      const keyBase64 = localStorage.getItem(`file_key_${fileId}`);
      if (!keyBase64) {
        throw new Error('Clé introuvable pour ce fichier');
      }
      const keyData = Uint8Array.from(atob(keyBase64), c => c.charCodeAt(0)).buffer;
      const key = await crypto.importKey(keyData);

      // Déchiffrer
      const decrypted = await crypto.decryptFile(encryptedData, key, iv);

      // Créer un blob et déclencher le téléchargement
      const decryptedBlob = new Blob([decrypted], { type: 'application/octet-stream' });
      const url = URL.createObjectURL(decryptedBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName || 'fichier';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert('Erreur lors du téléchargement ou déchiffrement');
    } finally {
      setDownloading(false);
    }
  };

  if (loading) return <div>Chargement...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="file-list">
      <h2>Mes fichiers</h2>
      {files.length === 0 ? (
        <p>Aucun fichier. <Link to="/upload">Uploader un fichier</Link></p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Nom</th>
              <th>Taille</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {files.map((file) => (
              <tr key={file.id}>
                <td>{file.name}</td>
                <td>{(file.size / 1024).toFixed(2)} Ko</td>
                <td>{new Date(file.created_at).toLocaleString()}</td>
                <td>
                  <button
                    onClick={() => handleDownload(file.id, file.name)}
                    disabled={downloading}
                    className="btn-primary btn-small"
                  >
                    Télécharger
                  </button>
                  <Link to={`/share/${file.id}`} className="btn-secondary btn-small">
                    Partager
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}