import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ModelMonitoringPage } from './ModelMonitoringPage';

const { getDashboardSummary, useModelStatus } = vi.hoisted(() => ({
  getDashboardSummary: vi.fn(),
  useModelStatus: vi.fn()
}));

vi.mock('@/api/dashboard', () => ({ getDashboardSummary }));
vi.mock('@/context/ModelStatusContext', () => ({ useModelStatus }));

const readyResponse = {
  status: 'ready',
  database_connected: true,
  database: 'connected',
  model_loaded: true,
  model_version: 'lightgbm_v2_weight_threshold_esi345',
  model_name: 'LightGBM V2 Weight + Threshold',
  model_source: 'final_registry',
  selected_calibration_method: 'raw_lightgbm_probability',
  threshold_config_loaded: true,
  decision_threshold: 0.60,
  feature_count: 273,
  class_order: ['ESI_3', 'ESI_4', 'ESI_5'],
  model_error: null,
  is_placeholder: false,
  timestamp: '2026-07-23T12:00:00Z',
  model_metrics: {
    accuracy: 0.7832381174458825,
    macro_f1: 0.7037018470872188,
    weighted_f1: 0.788775923531898,
    esi5_f1: 0.5469661610268378,
    unsafe_esi3_to_esi5_downgrade_rate: 0.006805735810832199
  }
};

describe('ModelMonitoringPage', () => {
  beforeEach(() => {
    getDashboardSummary.mockReset();
    getDashboardSummary.mockResolvedValue({
      recent_assessments: [],
      high_risk_flags: 0
    });
    useModelStatus.mockReset();
    useModelStatus.mockReturnValue({
      readiness: readyResponse,
      isLoading: false,
      error: null,
      readinessError: null,
      refresh: vi.fn()
    });
  });

  it('renders registry metrics and the explicit decision threshold', async () => {
    render(<ModelMonitoringPage />);

    expect(await screen.findByText('Decision threshold')).toBeInTheDocument();
    expect(screen.getByText('0.60')).toBeInTheDocument();
    expect(screen.getByText('78.32%')).toBeInTheDocument();
    expect(screen.getByText('70.37%')).toBeInTheDocument();
    expect(screen.getByText('78.88%')).toBeInTheDocument();
    expect(screen.getByText('54.70%')).toBeInTheDocument();
    expect(screen.getByText('0.68%')).toBeInTheDocument();
    expect(screen.getByText('Unsafe ESI 3→5 downgrade')).toBeInTheDocument();
    expect(screen.getByText('Lower is better')).toBeInTheDocument();
    expect(screen.getByText('Average prediction latency')).toBeInTheDocument();
    expect(screen.getByText('Prediction latency (ms) and confidence (%)')).toBeInTheDocument();
  });

  it('retains an honest unavailable state when registry metrics are absent', async () => {
    useModelStatus.mockReturnValue({
      readiness: { ...readyResponse, model_metrics: null },
      isLoading: false,
      error: null,
      readinessError: null,
      refresh: vi.fn()
    });

    render(<ModelMonitoringPage />);

    expect(await screen.findByText('No model metrics are available yet.')).toBeInTheDocument();
  });
});
