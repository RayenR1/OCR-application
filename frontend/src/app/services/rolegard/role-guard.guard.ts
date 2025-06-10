import { CanActivateFn, Router, UrlTree } from '@angular/router';
import { inject } from '@angular/core';
import { KeycloakService } from 'keycloak-angular';

export const RoleGuard = (requiredRoles: string[]): CanActivateFn => {
  return () => {
    const keycloak = inject(KeycloakService);
    const router = inject(Router);

    if (!keycloak.isLoggedIn()) {
      return router.createUrlTree(['/home']); // Redirige si non connecté
    }

    const userRoles = keycloak.getUserRoles(); // Retourne directement string[]
    const hasRequiredRole = requiredRoles.some(role => userRoles.includes(role));
    
    return hasRequiredRole ? true : router.createUrlTree(['/home']);
  };
};