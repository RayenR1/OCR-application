import 'leaflet';
import 'leaflet.heat';

declare module 'leaflet' {
  namespace heatLayer {
    function heat(latLngs: [number, number, number][], options?: any): any;
  }

  function heatLayer(latLngs: [number, number, number][], options?: any): any;
}