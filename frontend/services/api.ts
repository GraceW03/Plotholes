// API service for fetching heatmap data
const API_BASE_URL = 'http://localhost:3001'; // TODO change to actual backend deployment

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

export interface Report {
  idx: number;
  id: string;
  image_url: string;
  latitude: number;
  longitude: number;
  severity: number;
  severity_text: string;
  confidence: number;
  created_at: string;
}

export interface ReportsResponse {
  reports: Report[];
  count: number;
}

export interface NeighborhoodFeature {
  type: 'Feature';
  properties: {
    neighborhood: string;
    borough: string;
    issue_count: number;
    avg_severity: number;
    max_severity: number;
    risk_score: number;
    risk_level: string;
    color: string;
    opacity: number;
  };
  geometry: {
    type: 'Polygon';
    coordinates: number[][][];
  };
}

export interface IssuesResponse {
  issues: Issue[];
  count: number;
}

export interface NeighborhoodBoundariesResponse {
  type: 'FeatureCollection';
  features: NeighborhoodFeature[];
  count: number;
}

export const fetchIssues = async (): Promise<IssuesResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/issues`);
    if (!response.ok) {
      throw new Error('Failed to fetch issues');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching issues:', error);
    throw error;
  }
};

export const fetchReports = async (): Promise<ReportsResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/reports`);
    if (!response.ok) {
      throw new Error('Failed to fetch reports');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching reports:', error);
    throw error;
  }
};

export const fetchNeighborhoodBoundaries = async (): Promise<NeighborhoodBoundariesResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/neighborhood-boundaries`);
    if (!response.ok) {
      throw new Error('Failed to fetch neighborhood boundaries');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching neighborhood boundaries:', error);
    throw error;
  }
};