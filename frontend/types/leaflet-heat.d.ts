import * as L from 'leaflet';

declare module 'leaflet' {
  namespace L {
    function heatLayer(
      latlngs: Array<[number, number] | [number, number, number]>,
      options?: HeatMapOptions
    ): HeatLayer;

    interface HeatMapOptions {
      minOpacity?: number;
      maxZoom?: number;
      max?: number;
      radius?: number;
      blur?: number;
      gradient?: { [key: string]: string };
    }

    interface HeatLayer extends Layer {
      setLatLngs(latlngs: Array<[number, number] | [number, number, number]>): this;
      addLatLng(latlng: [number, number] | [number, number, number]): this;
      setOptions(options: HeatMapOptions): this;
      redraw(): this;
    }
  }
}

// Global declaration for when importing leaflet.heat
declare global {
  namespace L {
    function heatLayer(
      latlngs: Array<[number, number] | [number, number, number]>,
      options?: L.HeatMapOptions
    ): L.HeatLayer;

    interface HeatMapOptions {
      minOpacity?: number;
      maxZoom?: number;
      max?: number;
      radius?: number;
      blur?: number;
      gradient?: { [key: string]: string };
    }

    interface HeatLayer extends Layer {
      setLatLngs(latlngs: Array<[number, number] | [number, number, number]>): this;
      addLatLng(latlng: [number, number] | [number, number, number]): this;
      setOptions(options: HeatMapOptions): this;
      redraw(): this;
    }
  }
}

declare module 'leaflet.heat' {
  import * as L from 'leaflet';
  // This module extends Leaflet with heatLayer functionality
}