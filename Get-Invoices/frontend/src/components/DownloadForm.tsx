import React, { useState } from 'react';
import './DownloadForm.css';

interface DownloadResult {
  success: boolean;
  message: string;
  count: number;
  files: string[];
}

interface DownloadFormProps {
  onDownload: (maxInvoices: number, year?: number, month?: number) => void;
  loading: boolean;
  result: DownloadResult | null;
  error: string | null;
}

const DownloadForm: React.FC<DownloadFormProps> = ({
  onDownload,
  loading,
  result,
  error,
}) => {
  const [maxInvoices, setMaxInvoices] = useState<number>(100);
  const [year, setYear] = useState<number | ''>(new Date().getFullYear());
  const [month, setMonth] = useState<number | ''>('');

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    onDownload(
      maxInvoices,
      year ? Number(year) : undefined,
      month ? Number(month) : undefined
    );
  };

  const currentYear = new Date().getFullYear();

  return (
    <form onSubmit={handleSubmit} className="download-form">
      <div className="form-group">
        <label htmlFor="maxInvoices">
          Nombre maximum de factures à télécharger
        </label>
        <input
          id="maxInvoices"
          type="number"
          min="1"
          max="1000"
          value={maxInvoices}
          onChange={(e): void => setMaxInvoices(Number(e.target.value))}
          required
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="year">Année (optionnel)</label>
          <input
            id="year"
            type="number"
            min="2020"
            max={currentYear}
            value={year}
            onChange={(e): void => setYear(e.target.value ? Number(e.target.value) : '')}
          />
        </div>

        <div className="form-group">
          <label htmlFor="month">Mois (optionnel)</label>
          <select
            id="month"
            value={month}
            onChange={(e): void => setMonth(e.target.value ? Number(e.target.value) : '')}
          >
            <option value="">Tous les mois</option>
            <option value="1">Janvier</option>
            <option value="2">Février</option>
            <option value="3">Mars</option>
            <option value="4">Avril</option>
            <option value="5">Mai</option>
            <option value="6">Juin</option>
            <option value="7">Juillet</option>
            <option value="8">Août</option>
            <option value="9">Septembre</option>
            <option value="10">Octobre</option>
            <option value="11">Novembre</option>
            <option value="12">Décembre</option>
          </select>
        </div>
      </div>

      <button
        type="submit"
        className="download-button"
        disabled={loading}
      >
        {loading ? 'Téléchargement en cours...' : 'Télécharger les factures'}
      </button>

      {error && (
        <div className="error-message">
          <strong>Erreur:</strong> {error}
        </div>
      )}

      {result && (
        <div className={`result-message ${result.success ? 'success' : 'error'}`}>
          <strong>{result.success ? '✅ Succès' : '❌ Échec'}:</strong>{' '}
          {result.message}
          {result.files.length > 0 && (
            <div className="files-list">
              <strong>Fichiers téléchargés:</strong>
              <ul>
                {result.files.map((file, index) => (
                  <li key={index}>{file}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </form>
  );
};

export default DownloadForm;

