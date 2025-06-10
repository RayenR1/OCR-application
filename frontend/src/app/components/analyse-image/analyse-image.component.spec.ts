import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AnalyseImageComponent } from './analyse-image.component';

describe('AnalyseImageComponent', () => {
  let component: AnalyseImageComponent;
  let fixture: ComponentFixture<AnalyseImageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [AnalyseImageComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AnalyseImageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
