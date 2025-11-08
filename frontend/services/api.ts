// API service for fetching heatmap data
const API_BASE_URL = 'http://localhost:5000'; // TODO change to actual backend deployment

export interface Issue {
  unique_key: string;
  complaint_type: string;
  descriptor: string;
  status: string;
  borough: string;
  latitude: number;
  longitude: number;
  created_date: string;
  severity: number;
  incident_address: string;
}

export interface GridZone {
  id: string;
  bounds: {
    min_lat: number;
    min_lng: number;
    max_lat: number;
    max_lng: number;
  };
  center: {
    lat: number;
    lng: number;
  };
  issue_count: number;
  avg_severity: number;
  max_severity: number;
  risk_score: number;
  risk_level: string;
  accessibility_score: number;
  color: string;
  boroughs: string[];
}

export interface IssuesResponse {
  issues: Issue[];
  count: number;
}

export interface GridZonesResponse {
  zones: GridZone[];
  count: number;
  grid_size: number;
  grid_size_km: number;
}

export const fetchIssues = async (): Promise<IssuesResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/issues`);
    if (!response.ok) {
      throw new Error('Failed to fetch issues');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching issues:', error);
    throw error;
  }
};

export const fetchGridZones = async (gridSize: number = 0.01): Promise<GridZonesResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/grid-zones?grid_size=${gridSize}`);
    if (!response.ok) {
      throw new Error('Failed to fetch grid zones');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching grid zones:', error);
    throw error;
  }
};