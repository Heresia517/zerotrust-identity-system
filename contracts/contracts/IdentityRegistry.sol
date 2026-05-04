// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;
/**
* @title IdentityRegistry
* @author TOPAN Toé Hezekiah
* @notice Registre décentralisé d'identités pour architecture Zéro-Trust
* @dev Smart contract de gestion des identités DID sur Ethereum
*/
contract IdentityRegistry {
// ── STRUCTURES DE DONNÉES ──────────────────────────────────
struct Identite {
string  did;                  // DID W3C (did:ethr:0x...)
bool    actif;                // Statut actif/révoqué
uint256 dateEnregistrement;   // Timestamp Unix
uint256 dateRevocation;       // 0 si non révoquée
bytes32 hashDonneesChiffrees; // SHA-256 données off-chain

}
// ── VARIABLES D'ÉTAT ───────────────────────────────────────
mapping(address => Identite) private registre;
mapping(address => bool)     private administrateurs;
address public               proprietaire;
uint256 public               nombreIdentites;
// ── ÉVÉNEMENTS (pour auditabilité) ─────────────────────────
event IdentiteEnregistree(address indexed utilisateur, string did, uint256 date);
event IdentiteRevoquee(address indexed utilisateur, uint256 date);
event AdministrateurAjoute(address indexed admin);
// ── MODIFICATEURS ──────────────────────────────────────────
modifier seulementProprietaire() {
require(msg.sender == proprietaire, "Acces refuse : proprietaire uniquement");
_;
}
modifier seulementAdmin() {
require(administrateurs[msg.sender] || msg.sender == proprietaire,
"Acces refuse : administrateur requis");
_;
}
modifier identiteInexistante(address utilisateur) {
require(bytes(registre[utilisateur].did).length == 0,
"Identite deja enregistree");
_;
}
// ── CONSTRUCTEUR ───────────────────────────────────────────
constructor() {
proprietaire = msg.sender;
administrateurs[msg.sender] = true;
nombreIdentites = 0;
}
// ── FONCTIONS PRINCIPALES ──────────────────────────────────
/**
* @notice Enregistre une nouvelle identité dans le registre
* @param utilisateur Adresse Ethereum de l'utilisateur
* @param did Decentralized Identifier (did:ethr:0x...)
* @param hashDonnees Hash SHA-256 des données chiffrées off-chain
*/
function enregistrer(
address utilisateur,
string  calldata did,
bytes32 hashDonnees
) external seulementAdmin identiteInexistante(utilisateur) {
require(bytes(did).length > 0, "DID ne peut pas etre vide");
registre[utilisateur] = Identite({
did:                  did,
actif:                true,
dateEnregistrement:   block.timestamp,
dateRevocation:       0,
hashDonneesChiffrees: hashDonnees
});
nombreIdentites++;
emit IdentiteEnregistree(utilisateur, did, block.timestamp);
}
/**
* @notice Vérifie si une identité est valide et active
* @param utilisateur Adresse Ethereum à vérifier
* @return bool true si identité valide et active
*/
function verifier(address utilisateur) external view returns (bool) {
return registre[utilisateur].actif &&
bytes(registre[utilisateur].did).length > 0;
}
/**
* @notice Révoque une identité compromise ou expirée
* @param utilisateur Adresse Ethereum à révoquer
*/
function revoquer(address utilisateur) external seulementAdmin {
require(registre[utilisateur].actif, "Identite deja inactive");
registre[utilisateur].actif = false;
registre[utilisateur].dateRevocation = block.timestamp;
emit IdentiteRevoquee(utilisateur, block.timestamp);
}
/**
* @notice Retourne les détails complets d'une identité
* @param utilisateur Adresse Ethereum
* @return Identite struct complet
*/	
function obtenirIdentite(address utilisateur)
external view seulementAdmin returns (Identite memory)
{
return registre[utilisateur];
}
}
