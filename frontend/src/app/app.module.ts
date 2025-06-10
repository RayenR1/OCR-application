import { NgModule,DEFAULT_CURRENCY_CODE } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

import { MegaMenu } from 'primeng/megamenu';
import { ButtonModule } from 'primeng/button';
import { CommonModule } from '@angular/common';
import { AvatarModule } from 'primeng/avatar';
import { NavBarComponent } from './components/nav-bar/nav-bar.component';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { providePrimeNG } from 'primeng/config';
import Aura from '@primeng/themes/aura';
import { FooterComponent } from './components/footer/footer.component';
import { FormsModule } from '@angular/forms';
import { HomeComponent } from './components/home/home.component';
import { ContactComponent } from './components/contact/contact.component';
import { AbonnementComponent } from './components/abonnement/abonnement.component';
import { CardModule } from 'primeng/card';
import { getDarkModeSelector } from './services/theme'
import { TagModule } from 'primeng/tag';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { HttpClientModule } from '@angular/common/http';
import { InputTextModule } from 'primeng/inputtext';
import { MultiSelectModule } from 'primeng/multiselect';
import { SelectModule } from 'primeng/select';
import { TableModule } from 'primeng/table';
import { DialogModule } from 'primeng/dialog';
import { CheckboxModule } from 'primeng/checkbox';
import { ConfirmationService, MessageService } from 'primeng/api';
import { FileUploadModule } from 'primeng/fileupload';
import { ToastModule } from 'primeng/toast'; 
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ConfirmPopupModule } from 'primeng/confirmpopup';
import { DatePickerModule } from 'primeng/datepicker';
import { FluidModule } from 'primeng/fluid';
import { CalendarModule } from 'primeng/calendar';  
import { ChartModule } from 'primeng/chart';
import { OrderListModule } from 'primeng/orderlist';
import { DropdownModule } from 'primeng/dropdown';
import { StepperModule } from 'primeng/stepper';
import { IconField } from 'primeng/iconfield';
import { InputIcon } from 'primeng/inputicon';
import { ToggleButton } from 'primeng/togglebutton';
import { PasswordModule } from 'primeng/password';
import { AccordionModule } from 'primeng/accordion';
import { ProgressBar } from 'primeng/progressbar';
import { BadgeModule } from 'primeng/badge';
import { EditorModule } from 'primeng/editor';
import { SplitButton } from 'primeng/splitbutton';
import { StepsModule } from 'primeng/steps';

import { TooltipModule } from 'primeng/tooltip';





//import { KeycloakService } from './services/keycloack/keycloack.service';
import { APP_INITIALIZER } from '@angular/core';
import { HTTP_INTERCEPTORS, HttpClient } from '@angular/common/http'; 
import { HttpTokenInterceptor } from './services/interceptor/http-token.interceptor';
import { KeycloakAngularModule, KeycloakService } from 'keycloak-angular';
import { environment } from './environments/environment';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { AnalyseImageComponent } from './components/analyse-image/analyse-image.component';
import { ChatbotComponent } from './components/chatbot/chatbot.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { TarificationComponent } from './components/tarification/tarification.component';
export function initializeKeycloak(kcService: KeycloakService) {
  return () => 
    kcService.init({
      config: {
        url: environment.keycloak.url,
        realm: environment.keycloak.realm,
        clientId: environment.keycloak.clientId
      },
      initOptions: {
        onLoad: 'check-sso',
        checkLoginIframe: true,
        pkceMethod: 'S256',
        enableLogging: !environment.production,
        silentCheckSsoRedirectUri: 
          window.location.origin + '/silent-check-sso.html'
      }
    });}



@NgModule({
  declarations: [
    AppComponent,
    NavBarComponent,
    FooterComponent,
    HomeComponent,
    ContactComponent,
    AbonnementComponent,
    AnalyseImageComponent,
    ChatbotComponent,
    DashboardComponent,
    TarificationComponent
    
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    ButtonModule,
    CommonModule,
    AvatarModule,
    MegaMenu,
    FormsModule,
    CardModule,
    TableModule,
    SelectModule,
    MultiSelectModule,
    InputTextModule,
    IconFieldModule,
    InputIconModule,
    TagModule,
    HttpClientModule,
    DialogModule,
    CheckboxModule,
    FileUploadModule,
    ToastModule,
    ConfirmDialogModule,
    ConfirmPopupModule,
    DatePickerModule,
    FluidModule,
    CalendarModule,
    ChartModule,
    OrderListModule,
    DropdownModule,
    StepperModule,
    IconField,
    InputIcon,
    ToggleButton,
    PasswordModule,
    KeycloakAngularModule,
    ProgressSpinnerModule,
    AccordionModule,
    ProgressBar,
    BadgeModule,
    EditorModule,
    SplitButton,
    TooltipModule,
    StepsModule

    
  ],
  providers: [ provideAnimationsAsync(),
    ConfirmationService,
    MessageService,
    KeycloakService,
    providePrimeNG({
        theme: {
            preset: Aura,
            options: {
                prefix: 'p',
                darkModeSelector: getDarkModeSelector(),
                cssLayer: false
            }
        }
        
    }),
    HttpClient,
    {
      provide: HTTP_INTERCEPTORS,
      useClass: HttpTokenInterceptor,
      multi: true
    },
    { provide: APP_INITIALIZER, useFactory: initializeKeycloak, deps: [KeycloakService], multi: true },
    { 
      provide: DEFAULT_CURRENCY_CODE,
      useValue: 'EUR' 
    }],
  bootstrap: [AppComponent]
})
export class AppModule { 
}
