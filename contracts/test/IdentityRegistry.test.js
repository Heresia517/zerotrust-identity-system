// test/IdentityRegistry.test.js — Tests unitaires complets
const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("IdentityRegistry", function () {
  let contrat, proprietaire, utilisateur1, utilisateur2;
  const did1 = "did:ethr:0x742d35Cc6634C0532925a3b8D4C9C8F3";
  const hash1 = ethers.keccak256(ethers.toUtf8Bytes("donnees_chiffrees_user1"));

  beforeEach(async function () {
    [proprietaire, utilisateur1, utilisateur2] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("IdentityRegistry");
    contrat = await Factory.deploy();
  });

  // ── Tests : enregistrement ────────────────────────────────────
  describe("enregistrer()", function () {
    it("doit enregistrer une nouvelle identité", async function () {
      await contrat.enregistrer(utilisateur1.address, did1, hash1);
      expect(await contrat.nombreIdentites()).to.equal(1);
    });

    it("doit émettre l'événement IdentiteEnregistree", async function () {
      const tx = await contrat.enregistrer(utilisateur1.address, did1, hash1);
      const receipt = await tx.wait();
      // Recherche l'événement dans les logs
      const event = receipt.logs
        .map(log => {
          try {
            return contrat.interface.parseLog(log);
          } catch {
            return null;
          }
        })
        .find(parsed => parsed && parsed.name === "IdentiteEnregistree");
      expect(event).to.exist;
      expect(event.args[0]).to.equal(utilisateur1.address);
      expect(event.args[1]).to.equal(did1);
      // Le troisième argument (timestamp) n'est pas vérifié car il peut varier
    });

    it("doit rejeter un DID vide", async function () {
      await expect(
        contrat.enregistrer(utilisateur1.address, "", hash1),
      ).to.be.revertedWith("DID ne peut pas etre vide");
    });

    it("doit rejeter un double enregistrement", async function () {
      await contrat.enregistrer(utilisateur1.address, did1, hash1);
      await expect(
        contrat.enregistrer(utilisateur1.address, did1, hash1),
      ).to.be.revertedWith("Identite deja enregistree");
    });
  });

  // ── Tests : vérification ─────────────────────────────────────
  describe("verifier()", function () {
    it("doit retourner true pour une identité active", async function () {
      await contrat.enregistrer(utilisateur1.address, did1, hash1);
      expect(await contrat.verifier(utilisateur1.address)).to.equal(true);
    });

    it("doit retourner false pour une adresse inconnue", async function () {
      expect(await contrat.verifier(utilisateur2.address)).to.equal(false);
    });

    it("doit retourner false après révocation", async function () {
      await contrat.enregistrer(utilisateur1.address, did1, hash1);
      await contrat.revoquer(utilisateur1.address);
      expect(await contrat.verifier(utilisateur1.address)).to.equal(false);
    });
  });

  // ── Tests : contrôle d'accès ──────────────────────────────────
  describe("Contrôle d'accès", function () {
    it("doit rejeter un enregistrement par non-admin", async function () {
      await expect(
        contrat
          .connect(utilisateur1)
          .enregistrer(utilisateur2.address, did1, hash1),
      ).to.be.revertedWith("Acces refuse : administrateur requis");
    });
  });
});