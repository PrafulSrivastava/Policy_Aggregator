import { PolicyChange, RouteSubscription, SourceConfig, Stats } from './types';

export const MOCK_STATS: Stats = {
  totalRoutes: 5,
  activeSources: 12,
  changesThisMonth: 8
};

export const MOCK_ROUTES: RouteSubscription[] = [
  {
    id: 1,
    originCountry: "India",
    destinationCountry: "Germany",
    visaType: "Student",
    createdAt: "2025-01-15",
    lastChangeDetected: "2025-01-27 14:30",
    associatedSourcesCount: 3
  },
  {
    id: 2,
    originCountry: "USA",
    destinationCountry: "UK",
    visaType: "Skilled Worker",
    createdAt: "2024-11-20",
    lastChangeDetected: "2025-01-10 09:15",
    associatedSourcesCount: 2
  },
  {
    id: 3,
    originCountry: "Canada",
    destinationCountry: "France",
    visaType: "Tech Visa",
    createdAt: "2024-12-05",
    associatedSourcesCount: 1
  }
];

export const MOCK_SOURCES: SourceConfig[] = [
  {
    id: 1,
    name: "German Embassy India",
    country: "Germany",
    visaType: "Student",
    url: "https://www.india.diplo.de/visa",
    fetchType: "HTML",
    checkFrequency: "Daily",
    lastChecked: "2025-01-27 15:00",
    lastChangeDetected: "2025-01-27 14:30",
    status: "Healthy"
  },
  {
    id: 2,
    name: "UK Home Office",
    country: "UK",
    visaType: "Skilled Worker",
    url: "https://www.gov.uk/skilled-worker-visa",
    fetchType: "HTML",
    checkFrequency: "Daily",
    lastChecked: "2025-01-27 14:45",
    lastChangeDetected: "2025-01-10 09:15",
    status: "Healthy"
  },
  {
    id: 3,
    name: "France-Visas",
    country: "France",
    visaType: "Tech Visa",
    url: "https://france-visas.gouv.fr/",
    fetchType: "PDF",
    checkFrequency: "Weekly",
    lastChecked: "2025-01-20 10:00",
    lastChangeDetected: "Never",
    status: "Stale"
  },
  {
    id: 4,
    name: "Legacy Portal",
    country: "Germany",
    visaType: "Work",
    url: "https://legacy.example.com",
    fetchType: "HTML",
    checkFrequency: "Daily",
    lastChecked: "2025-01-27 15:05",
    lastChangeDetected: "Never",
    status: "Error"
  }
];

export const MOCK_CHANGES: PolicyChange[] = [
  {
    id: 123,
    detectedAt: "2025-01-27 14:30",
    route: {
      origin: "India",
      destination: "Germany",
      visaType: "Student"
    },
    sourceName: "German Embassy India",
    sourceUrl: "https://www.india.diplo.de/visa",
    lastChecked: "2025-01-27 15:00",
    changePreview: "+ Updated visa processing time from 4-6 weeks to 6-8 weeks\n- Removed requirement for bank statement\n+ Added requirement for health insurance certificate",
    diff: `- Processing time: 4-6 weeks
+ Processing time: 6-8 weeks
  Applicants must submit:
  1. Valid Passport
- 2. Bank Statement (last 3 months)
+ 2. Health Insurance Certificate (minimum coverage €30,000)
  3. Letter of Acceptance`,
    aiSummary: "The visa processing time has been extended from 4-6 weeks to 6-8 weeks. Additionally, the requirement for a bank statement has been replaced by a mandatory health insurance certificate with minimum coverage of €30,000.",
    impactAssessment: {
      score: "High",
      explanation: "This change affects all new student visa applications and requires applicants to obtain new insurance documentation, potentially delaying submissions."
    }
  },
  {
    id: 124,
    detectedAt: "2025-01-10 09:15",
    route: {
      origin: "USA",
      destination: "UK",
      visaType: "Skilled Worker"
    },
    sourceName: "UK Home Office",
    sourceUrl: "https://www.gov.uk/skilled-worker-visa",
    lastChecked: "2025-01-27 14:45",
    changePreview: "+ Salary threshold increased to £38,700\n- Shortage occupation list removed",
    diff: `  Eligibility requirements:
  You must have a job offer from an approved sponsor.
- The minimum salary is £26,200.
+ The minimum salary is £38,700.
- Check if your job is on the shortage occupation list.
+ The shortage occupation list has been replaced by the Immigration Salary List.`,
    aiSummary: "The minimum salary threshold for Skilled Worker visas has increased significantly from £26,200 to £38,700. The Shortage Occupation List has also been replaced by the Immigration Salary List.",
    impactAssessment: {
      score: "Medium",
      explanation: "Applicants earning between the old and new thresholds may no longer qualify. Employers must review current salary offers."
    }
  }
];

export const COUNTRIES = ["India", "Germany", "USA", "UK", "Canada", "France", "Australia", "Japan"];
export const VISA_TYPES = ["Student", "Work", "Tourist", "Business", "Skilled Worker", "Tech Visa"];