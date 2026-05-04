# tests/dos_simulator.py
import asyncio
import aiohttp
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def requete_attaque(session, url):
    try:
        async with session.post(url, data={
            'grant_type': 'password',
            'client_id': 'zt-frontend-client',
            'username': 'attaquant',
            'password': 'motdepasse_invalide'
        }, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            return resp.status
    except asyncio.TimeoutError:
        logger.warning("Requête timeout")
        return 0
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        return 0

async def lancer_attaque_dos(url, nb_requetes=1000):
    async with aiohttp.ClientSession() as session:
        taches = [requete_attaque(session, url) for _ in range(nb_requetes)]
        debut = time.time()
        resultats = await asyncio.gather(*taches)
        duree = time.time() - debut
        print(f'DoS : {nb_requetes} requêtes en {duree:.2f}s')
        print(f'Codes retour : {set(resultats)}')

if __name__ == "__main__":
    url = "http://localhost:8080/realms/zt-decentralized-iam/protocol/openid-connect/token"
    asyncio.run(lancer_attaque_dos(url))