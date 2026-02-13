import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

interface DownloadResponse {
  success: boolean;
  message: string;
  count: number;
  files: string[];
}

interface StatusResponse {
  status: string;
  message: string;
}

interface OTPResponse {
  success: boolean;
  message: string;
  requires_otp: boolean;
}

export const getStatus = async (): Promise<StatusResponse> => {
  const response = await axios.get<StatusResponse>(`${API_BASE_URL}/api/status`);
  return response.data;
};

export const downloadInvoices = async (
  maxInvoices: number,
  year?: number,
  month?: number
): Promise<DownloadResponse> => {
  const response = await axios.post<DownloadResponse>(
    `${API_BASE_URL}/api/download`,
    {
      max_invoices: maxInvoices,
      year: year,
      month: month,
    }
  );
  return response.data;
};

export const submitOTP = async (otpCode: string): Promise<OTPResponse> => {
  const response = await axios.post<OTPResponse>(
    `${API_BASE_URL}/api/submit-otp`,
    {
      otp_code: otpCode,
    }
  );
  return response.data;
};

export const check2FA = async (): Promise<OTPResponse> => {
  const response = await axios.get<OTPResponse>(`${API_BASE_URL}/api/check-2fa`);
  return response.data;
};

