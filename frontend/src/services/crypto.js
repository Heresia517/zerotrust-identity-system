/**
 * Module de chiffrement côté client (E2EE) avec Web Crypto API
 */

// Génère une clé AES-256-GCM aléatoire
export async function generateKey() {
  return await crypto.subtle.generateKey(
    { name: 'AES-GCM', length: 256 },
    true, // extractable (pour pouvoir l'exporter)
    ['encrypt', 'decrypt']
  );
}

// Exporte une clé au format ArrayBuffer (raw)
export async function exportKey(key) {
  return await crypto.subtle.exportKey('raw', key);
}

// Importe une clé depuis un ArrayBuffer
export async function importKey(keyData) {
  return await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'AES-GCM', length: 256 },
    true,
    ['encrypt', 'decrypt']
  );
}

// Chiffre un fichier avec une clé
// Retourne { encrypted: ArrayBuffer, iv: Uint8Array }
export async function encryptFile(file, key) {
  const iv = crypto.getRandomValues(new Uint8Array(12)); // 96 bits
  const data = await file.arrayBuffer();

  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    data
  );

  return { encrypted, iv };
}

// Déchiffre des données
export async function decryptFile(encryptedData, key, iv) {
  return await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv },
    key,
    encryptedData
  );
}

// Calcule le hash SHA-256 d'un ArrayBuffer
export async function hashFile(data) {
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}