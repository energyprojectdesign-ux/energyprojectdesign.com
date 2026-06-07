/* Gas Natural Studio — calc widgets shared utilities. */
import api from '../lib/api';

export async function runCalc(calc, params) {
  const { data } = await api.post('/gas-project/calc', { calc, params });
  return data;
}

export const REGIME_OPTIONS = [
  { value: 'joasa', label: 'Presiune joasă (≤100 mbar)' },
  { value: 'medie', label: 'Presiune medie (>100 mbar – 6 bar)' },
];

export const MATERIAL_OPTIONS = [
  'PE 100 SDR 11', 'PE 100 SDR 17.6', 'OL galvanizat', 'Cupru',
];

export const ZONE_OPTIONS = [
  { value: 'trafic_auto', label: 'Sub trafic auto (min 1.0 m)' },
  { value: 'trotuar', label: 'Sub trotuar (min 0.9 m)' },
  { value: 'spatii_verzi', label: 'Spații verzi (min 0.6 m)' },
];
