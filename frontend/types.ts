export interface RouteSubscription {
  id: number;
  originCountry: string;
  destinationCountry: string;
  visaType: string;
  createdAt: string;
  lastChangeDetected?: string;
  associatedSourcesCount: number;
}

export interface SourceConfig {
  id: number;
  name: string;
  country: string;
  visaType: string;
  url: string;
  fetchType: 'HTML' | 'PDF';
  checkFrequency: 'Daily' | 'Weekly' | 'Custom';
  lastChecked: string;
  lastChangeDetected: string;
  status: 'Healthy' | 'Stale' | 'Error';
}

export interface PolicyChange {
  id: number;
  detectedAt: string;
  route: {
    origin: string;
    destination: string;
    visaType: string;
  };
  sourceName: string;
  sourceUrl: string;
  changePreview: string;
  diff: string;
  lastChecked: string;
  aiSummary?: string;
  impactAssessment?: {
    score: 'High' | 'Medium' | 'Low';
    explanation: string;
  };
}

export interface Stats {
  totalRoutes: number;
  activeSources: number;
  changesThisMonth: number;
}

export type FetchResult = {
  success: boolean;
  fetchedAt: string;
  duration: number;
  contentHash: string;
  contentLength: number;
  contentPreview: string;
  changeDetected: boolean;
  previousHash?: string;
  diffPreview?: string;
  errorType?: string;
  errorMessage?: string;
};