import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TarificationComponent } from './tarification.component';

describe('TarificationComponent', () => {
  let component: TarificationComponent;
  let fixture: ComponentFixture<TarificationComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [TarificationComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TarificationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
