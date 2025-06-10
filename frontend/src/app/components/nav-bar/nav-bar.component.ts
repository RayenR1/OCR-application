import { Component ,OnInit } from '@angular/core';
import { Router,ActivatedRoute } from '@angular/router';
import { KeycloakService } from 'keycloak-angular';

@Component({
  selector: 'app-nav-bar',
  standalone: false,
  templateUrl: './nav-bar.component.html',
  styleUrl: './nav-bar.component.css'
})
export class NavBarComponent implements OnInit {
  items: any[] | undefined;
  isLoggedIn: boolean = false;
  isDarkTheme!: boolean ;
  userRoles: string[] = [];
  constructor(private activatedRoute: ActivatedRoute,private router: Router,private keycloakService: KeycloakService ) { }

  async ngOnInit() {
    this.isDarkTheme = localStorage.getItem('user-theme') === 'dark';
    await this.checkAuthStatus();
    this.buildMenu();
  }

  private async checkAuthStatus() {
    this.isLoggedIn = await this.keycloakService.isLoggedIn();
    if (this.isLoggedIn) {
      this.userRoles = this.keycloakService.getUserRoles();
    }
  }


  private buildMenu() {
    const baseItems = [
      {
        label: 'Home',
        root: true,
        link: '/home'
      },
      {
        label: 'Contact',
        root: true,
        link: '/contact'
      },
      {
        label: 'Subscription',
        root: true,
        link: '/subscribe'
      }
    ];
    const analysisItems = {
      label: 'Analyse',
      root: true,
      items: [
        [
          {
            items: [
              { label: 'Analyse image', icon: 'pi pi-image', subtext: 'extract text', link: '/analyse/image' },
            ]
          }
        ],
        [
          {
            items: [
              { label: 'Analyse Tarification', icon: 'pi-money-bill', subtext: 'tarification summary', link: 'analyse/TarificationComponent' }
            ]
          }
        ],
        [
          {
            items: [
              { label: 'Analyse Fraude', icon: 'pi pi-search', subtext: 'chat bot', link: '/analyse/chatbot' },
            ]
          }
        ]
      ],
      link: '/analyse'
    };

    const dataManagementItems = {
      label: 'Data Management',
      root: true,
      items: [
        [
          {
            items: [
              { label: 'document Dashboard', icon: 'pi pi-list', subtext: 'Subtext of item', link: 'analyse/dashboard' }
              
            ]
          }
        ]
      ],
      link: '/data'
    };

    this.items = [...baseItems];
    
    if  (this.isLoggedIn) {   /// 
      if (true) {
        this.items.push(analysisItems);
      }
      if (true) {
        this.items.push(dataManagementItems);
      }
    }
  }

  hasRole(role: string): boolean {
    return this.userRoles.includes(role);
  }

  
  async login() {
    await this.keycloakService.login({
      redirectUri: window.location.origin + '/home'
    });
    this.isLoggedIn = true;
    this.buildMenu();
  }

  async logout() {
    await this.keycloakService.logout(window.location.origin);
    this.isLoggedIn = false;
    this.buildMenu();
  }

  
  async manageAccount() {
    try {
      
      const keycloakInstance = this.keycloakService.getKeycloakInstance();
      await keycloakInstance.accountManagement();
    } catch (error) {
      console.error('Erreur de gestion du compte:', error);
    }
  }


    isActiveRoute(route: string): boolean {
    return  this.router.url.includes(route);
    }
    isActiveRoute2(route: string): boolean {
        return  this.router.url.endsWith(route);
    }

    toggleTheme() {
        this.isDarkTheme = !this.isDarkTheme;
        localStorage.getItem('user-theme');
        localStorage.setItem('user-theme', this.isDarkTheme ? 'dark' : 'light');
        window.location.reload();
    }
    
}
