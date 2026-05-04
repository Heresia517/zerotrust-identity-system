// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title Permissions
 * @dev Contrat de gestion des permissions pour les fichiers dans une architecture Zero-Trust.
 * Implémente un contrôle d'accès basé sur les rôles (RBAC) avec niveaux de permission,
 * expiration et traçabilité via événements.
 */
contract Permissions {
    // --- Types ---
    enum PermissionLevel { NONE, READ, WRITE, DELETE, ADMIN }

    struct Permission {
        address grantee;           // Adresse du bénéficiaire
        PermissionLevel level;      // Niveau de permission
        uint256 expiresAt;          // Timestamp d'expiration (0 = jamais)
        bool isActive;              // État (révoqué ou non)
    }

    // --- Variables d'état ---
    address public owner;                       // Propriétaire du contrat (déployeur)
    uint256 public fileCounter;                  // Compteur pour générer des IDs uniques
    mapping(uint256 => address) public fileOwners;           // fileId => owner address
    mapping(uint256 => mapping(address => Permission)) public permissions; // fileId => grantee => Permission
    mapping(uint256 => bool) public fileExists;               // fileId => existence

    // --- Événements pour l'audit trail ---
    event FileRegistered(uint256 indexed fileId, address indexed owner, uint256 timestamp);
    event PermissionGranted(uint256 indexed fileId, address indexed grantee, PermissionLevel level, uint256 expiresAt, uint256 timestamp);
    event PermissionRevoked(uint256 indexed fileId, address indexed grantee, uint256 timestamp);
    event PermissionChanged(uint256 indexed fileId, address indexed grantee, PermissionLevel newLevel, uint256 newExpiresAt, uint256 timestamp);
    event OwnershipTransferred(uint256 indexed fileId, address indexed previousOwner, address indexed newOwner, uint256 timestamp);

    // --- Modificateurs ---
    modifier onlyOwner(uint256 fileId) {
        require(msg.sender == fileOwners[fileId], "Permissions: caller is not the owner");
        _;
    }

    modifier fileExistsModifier(uint256 fileId) {
        require(fileExists[fileId], "Permissions: file does not exist");
        _;
    }

    // --- Constructeur ---
    constructor() {
        owner = msg.sender;
    }

    // --- Fonctions principales ---

    /**
     * @dev Enregistre un nouveau fichier dans le contrat.
     * @return fileId L'identifiant unique du fichier.
     */
    function registerFile() external returns (uint256 fileId) {
        fileId = fileCounter;
        fileOwners[fileId] = msg.sender;
        fileExists[fileId] = true;
        fileCounter++;

        // Accorder automatiquement la permission ADMIN au propriétaire
        permissions[fileId][msg.sender] = Permission({
            grantee: msg.sender,
            level: PermissionLevel.ADMIN,
            expiresAt: 0,
            isActive: true
        });

        emit FileRegistered(fileId, msg.sender, block.timestamp);
        return fileId;
    }

    /**
     * @dev Accorde une permission sur un fichier à un bénéficiaire.
     * @param fileId Identifiant du fichier.
     * @param grantee Adresse du bénéficiaire.
     * @param level Niveau de permission.
     * @param expiresAt Timestamp d'expiration (0 = jamais).
     */
    function grantPermission(
        uint256 fileId,
        address grantee,
        PermissionLevel level,
        uint256 expiresAt
    ) external onlyOwner(fileId) fileExistsModifier(fileId) {
        require(grantee != address(0), "Permissions: invalid grantee address");
        require(level != PermissionLevel.NONE, "Permissions: cannot grant NONE level");
        require(expiresAt == 0 || expiresAt > block.timestamp, "Permissions: expiration must be in the future");

        Permission storage perm = permissions[fileId][grantee];
        perm.grantee = grantee;
        perm.level = level;
        perm.expiresAt = expiresAt;
        perm.isActive = true;

        emit PermissionGranted(fileId, grantee, level, expiresAt, block.timestamp);
    }

    /**
     * @dev Vérifie si un utilisateur a une permission suffisante pour une action.
     * @param fileId Identifiant du fichier.
     * @param user Adresse de l'utilisateur.
     * @param requiredLevel Niveau de permission requis.
     * @return bool True si la permission est valide.
     */
    function checkPermission(
        uint256 fileId,
        address user,
        PermissionLevel requiredLevel
    ) external view fileExistsModifier(fileId) returns (bool) {
        Permission memory perm = permissions[fileId][user];
        if (!perm.isActive) return false;
        if (perm.expiresAt != 0 && perm.expiresAt <= block.timestamp) return false;
        // ADMIN peut tout faire
        if (perm.level == PermissionLevel.ADMIN) return true;
        // Sinon, on compare les niveaux (READ < WRITE < DELETE < ADMIN)
        return uint8(perm.level) >= uint8(requiredLevel);
    }

    /**
     * @dev Révoque une permission (désactive sans supprimer l'entrée).
     * @param fileId Identifiant du fichier.
     * @param grantee Adresse du bénéficiaire.
     */
    function revokePermission(uint256 fileId, address grantee) external onlyOwner(fileId) fileExistsModifier(fileId) {
        require(grantee != msg.sender, "Permissions: cannot revoke own admin permission");
        Permission storage perm = permissions[fileId][grantee];
        require(perm.isActive, "Permissions: permission already revoked");
        perm.isActive = false;
        emit PermissionRevoked(fileId, grantee, block.timestamp);
    }

    /**
     * @dev Modifie une permission existante (niveau et expiration).
     * @param fileId Identifiant du fichier.
     * @param grantee Adresse du bénéficiaire.
     * @param newLevel Nouveau niveau.
     * @param newExpiresAt Nouvelle date d'expiration.
     */
    function modifyPermission(
        uint256 fileId,
        address grantee,
        PermissionLevel newLevel,
        uint256 newExpiresAt
    ) external onlyOwner(fileId) fileExistsModifier(fileId) {
        require(grantee != address(0), "Permissions: invalid grantee");
        require(newLevel != PermissionLevel.NONE, "Permissions: cannot set NONE level");
        require(newExpiresAt == 0 || newExpiresAt > block.timestamp, "Permissions: expiration must be in the future");

        Permission storage perm = permissions[fileId][grantee];
        require(perm.isActive, "Permissions: cannot modify inactive permission");

        perm.level = newLevel;
        perm.expiresAt = newExpiresAt;

        emit PermissionChanged(fileId, grantee, newLevel, newExpiresAt, block.timestamp);
    }

    /**
     * @dev Récupère le niveau de permission actif pour un utilisateur.
     * @param fileId Identifiant du fichier.
     * @param user Adresse de l'utilisateur.
     * @return PermissionLevel Niveau effectif (NONE si aucune permission valide).
     */
    function getPermissionLevel(uint256 fileId, address user) external view fileExistsModifier(fileId) returns (PermissionLevel) {
        Permission memory perm = permissions[fileId][user];
        if (!perm.isActive) return PermissionLevel.NONE;
        if (perm.expiresAt != 0 && perm.expiresAt <= block.timestamp) return PermissionLevel.NONE;
        return perm.level;
    }

    /**
     * @dev Transfère la propriété d'un fichier à un nouveau propriétaire.
     * @param fileId Identifiant du fichier.
     * @param newOwner Adresse du nouveau propriétaire.
     */
    function transferOwnership(uint256 fileId, address newOwner) external onlyOwner(fileId) fileExistsModifier(fileId) {
        require(newOwner != address(0), "Permissions: invalid new owner");
        require(newOwner != msg.sender, "Permissions: new owner must be different");

        address previousOwner = fileOwners[fileId];
        fileOwners[fileId] = newOwner;

        // Accorder automatiquement ADMIN au nouveau propriétaire
        permissions[fileId][newOwner] = Permission({
            grantee: newOwner,
            level: PermissionLevel.ADMIN,
            expiresAt: 0,
            isActive: true
        });

        // Ne pas révoquer l'ancien propriétaire, mais il perd le rôle onlyOwner
        emit OwnershipTransferred(fileId, previousOwner, newOwner, block.timestamp);
    }

    /**
     * @dev Vérifie si une adresse est propriétaire d'un fichier.
     * @param fileId Identifiant du fichier.
     * @param user Adresse à vérifier.
     * @return bool True si l'utilisateur est propriétaire.
     */
    function isOwner(uint256 fileId, address user) external view returns (bool) {
        return fileExists[fileId] && fileOwners[fileId] == user;
    }
}