import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AppComponent } from './app.component';
import { HomeComponent } from './components/home/home.component';
import { ContactComponent } from './components/contact/contact.component';
import { AbonnementComponent } from './components/abonnement/abonnement.component';
import { AnalyseImageComponent } from './components/analyse-image/analyse-image.component';
import { AuthGuard } from './services/authGard/auth.guard';
import { ChatbotComponent } from './components/chatbot/chatbot.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { TarificationComponent } from './components/tarification/tarification.component';

import { RoleGuard } from './services/rolegard/role-guard.guard';



const routes: Routes = [
  { path: '',
    redirectTo: 'home', pathMatch: 'full' },
  {
    path:'contact',
    component: ContactComponent
  },
  {
    path: 'app',
    component: AppComponent
  },
  {
    path: 'home',
    component: HomeComponent
  },
  {
    path:'subscribe',
    component: AbonnementComponent
  },
  {
    path:'analyse/image',
    component: AnalyseImageComponent,
    canActivate: [AuthGuard]
  },
  {
    path:'analyse/chatbot',
    component: ChatbotComponent,
    canActivate: [AuthGuard]
  },{
    path:'analyse/dashboard',
    component: DashboardComponent,
    canActivate: [AuthGuard]
  },
  {
    path:'analyse/TarificationComponent',
    component: TarificationComponent,
    canActivate: [AuthGuard]
  }

];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
