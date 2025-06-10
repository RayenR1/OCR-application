import { CanActivateFn, Router,UrlTree } from '@angular/router';
import { inject } from '@angular/core';
import { KeycloakService } from 'keycloak-angular';

export const AuthGuard = () => {
  const keycloak = inject(KeycloakService);
  return keycloak.isLoggedIn();
};