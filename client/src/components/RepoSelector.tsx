import React from 'react';
import { AnalysisProvider, useAnalysis } from '../context/AnalysisContext';
import { SelectionScreen } from './SelectionScreen';
import { Dashboard } from './Dashboard';
import { AnalysisView } from './AnalysisView';

const AppContent: React.FC = () => {
    const { showProjectInfo, isAnalyzing } = useAnalysis();

    if (isAnalyzing) {
        return <AnalysisView />;
    }

    return showProjectInfo ? <Dashboard /> : <SelectionScreen />;
};

export default function RepoSelector() {
    return (
        <AnalysisProvider>
            <AppContent />
        </AnalysisProvider>
    );
}
