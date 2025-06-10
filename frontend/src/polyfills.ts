/***************************************************************************************************
 * BROWSER POLYFILLS
 **************************************************************************************************/

// Définir l'objet `global` pour les navigateurs
(window as any).global = window;

// Polyfills pour les navigateurs anciens (IE9, IE10, IE11)
import 'core-js/stable'; // Importe tous les polyfills de core-js

// Zone.js (nécessaire pour Angular)
import 'zone.js'; // Importe zone.js

/***************************************************************************************************
 * APPLICATION IMPORTS
 */

// Ajoutez ici vos polyfills personnalisés si nécessaire.