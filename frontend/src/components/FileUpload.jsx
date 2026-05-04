import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import * as crypto from '../services/crypto';
import { uploadFile } from '../services/api';

export default function FileUpload() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError('');
    setProgress(10);
    try {
      // 1. Générer une clé AES
      const key = await crypto.generateKey();
      // 2. Chiffrer le fichier
      const { encrypted, iv } = await crypto.encryptFile(file, key);
      setProgress(50);
      // 3. Concaténer IV + données chiffrées
      const ivArray = new Uint8Array(iv);
      const encryptedArray = new Uint8Array(encrypted);
      const combined = new Uint8Array(ivArray.length + encryptedArray.length);
      combined.set(ivArray, 0);
      combined.set(encryptedArray, ivArray.length);
      const blob = new Blob([combined], { type: 'application/octet-stream' });
      // 4. Créer un FormData et uploader
      const formData = new FormData();
      formData.append('file', blob, file.name);
      const { data } = await uploadFile(formData);
      setProgress(100);
      // 5. Sauvegarder la clé (simulation) - en prod, le backend stocke dans Vault
      const exportedKey = await crypto.exportKey(key);
      localStorage.setItem(`file_key_${data.id}`, btoa(String.fromCharCode(...new Uint8Array(exportedKey))));
      // 6. Rediriger
      navigate('/files');
    } catch (err) {
      console.error(err);
      setError('Erreur lors de l\'upload');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="file-upload">
      <h2>Uploader un fichier</h2>
      <div className="card">
        <input type="file" onChange={handleFileChange} disabled={uploading} />
        {file && (
          <div className="file-info">
            <p>Fichier : {file.name} ({(file.size / 1024).toFixed(2)} Ko)</p>
            <button onClick={handleUpload} disabled={uploading} className="btn-primary">
              {uploading ? 'Upload en cours...' : 'Chiffrer et uploader'}
            </button>
          </div>
        )}
        {uploading && (
          <div className="progress">
            <div className="progress-bar" style={{ width: `${progress}%` }}></div>
          </div>
        )}
        {error && <div className="error">{error}</div>}
      </div>
    </div>
  );
}