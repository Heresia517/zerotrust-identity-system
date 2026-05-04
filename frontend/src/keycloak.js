import Keycloak from 'keycloak-js';

const keycloak = new Keycloak({
    url: 'http://localhost:8080',
    realm: 'zt-decentralized-iam',
    clientId: 'zt-frontend-client'
});

export default keycloak;