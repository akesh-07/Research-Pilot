import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, Loader2, Globe, Check, BookOpen } from 'lucide-react';
import api from '../services/api';

const ACADEMIC_SOURCES = [
  {
    id: 'arxiv',
    name: 'arXiv',
    tag: 'Preprints',
    desc: 'AI, Machine Learning, Computer Science, Physics & Mathematics',
    badgeClass: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
    borderActiveClass: 'border-purple-500 shadow-purple-500/10'
  },
  {
    id: 'pubmed',
    name: 'PubMed',
    tag: 'Biomedical & Clinical',
    desc: 'Medicine, Genetics, Healthcare & Life Sciences (NCBI)',
    badgeClass: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
    borderActiveClass: 'border-emerald-500 shadow-emerald-500/10'
  },
  {
    id: 'openalex',
    name: 'OpenAlex',
    tag: 'Universal (250M+ Papers)',
    desc: 'Comprehensive open index of global research across all scientific domains',
    badgeClass: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40',
    borderActiveClass: 'border-cyan-500 shadow-cyan-500/10'
  },
  {
    id: 'crossref',
    name: 'Crossref',
    tag: 'Peer-Reviewed Journals',
    desc: 'Official DOI registry (Nature, Science, IEEE, Elsevier, Springer)',
    badgeClass: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
    borderActiveClass: 'border-amber-500 shadow-amber-500/10'
  }
];

export default function ResearchInput() {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const [loading, setLoading] = useState(false);
  const [files, setFiles] = useState([]);
  const [selectedSources, setSelectedSources] = useState(['arxiv', 'pubmed', 'openalex', 'crossref']);
  const navigate = useNavigate();

  const toggleSource = (sourceId) => {
    setSelectedSources(prev => {
      if (prev.includes(sourceId)) {
        if (prev.length === 1) return prev; // Keep at least one selected
        return prev.filter(s => s !== sourceId);
      } else {
        return [...prev, sourceId];
      }
    });
  };

  const toggleAllSources = () => {
    if (selectedSources.length === ACADEMIC_SOURCES.length) {
      setSelectedSources(['arxiv']);
    } else {
      setSelectedSources(ACADEMIC_SOURCES.map(s => s.id));
    }
  };

  const onSubmit = async (data) => {
    if (selectedSources.length === 0) {
      alert("Please select at least one academic literature source.");
      return;
    }

    setLoading(true);
    try {
      // Step 1: Submit Research Parameters and Upload Files
      const formData = new FormData();
      formData.append('research_question', data.research_question);
      if (data.goals) formData.append('goals', data.goals);
      if (data.constraints) formData.append('constraints', data.constraints);
      formData.append('sources', JSON.stringify(selectedSources));
      
      Array.from(files).forEach(file => {
        formData.append('files', file);
      });

      const uploadRes = await api.post('/research/submit', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // Step 2: Trigger Supervisor Agent to Generate Tasks
      const supervisorPayload = {
        research_question: uploadRes.data.research_question,
        goals: data.goals,
        constraints: data.constraints,
        sources: selectedSources,
        uploaded_files: uploadRes.data.uploaded_files
      };

      const supervisorRes = await api.post('/supervisor/tasks', supervisorPayload);
      
      // Step 3: Navigate to Task Board with state
      navigate('/tasks', { state: { workflow: supervisorRes.data, researchContext: supervisorPayload } });
    } catch (error) {
      console.error("Error submitting research:", error);
      alert("Failed to submit research or generate plan. Check console for details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold mb-2">Start a New Research Mission</h1>
        <p className="text-textSecondary">Provide your objectives, choose open academic databases, and let the agents plan and discover.</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="card space-y-6">
        {/* Core Question */}
        <div>
          <label className="block text-sm font-medium mb-2">Research Question *</label>
          <textarea 
            {...register("research_question", { required: "This is required" })}
            className="input-field min-h-[100px]"
            placeholder="What is the core question you are trying to answer? (e.g. Graph neural networks for Alzheimer's drug discovery)"
          />
          {errors.research_question && <span className="text-red-400 text-sm mt-1">{errors.research_question.message}</span>}
        </div>

        {/* Goals & Constraints */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium mb-2">Goals</label>
            <textarea 
              {...register("goals")}
              className="input-field min-h-[80px]"
              placeholder="E.g., Publish a survey, discover candidate targets..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Constraints</label>
            <textarea 
              {...register("constraints")}
              className="input-field min-h-[80px]"
              placeholder="E.g., Focus on post-2021 literature, human clinical trials..."
            />
          </div>
        </div>

        {/* Multi-Source Academic Database Selection Checkboxes */}
        <div className="space-y-3 pt-2">
          <div className="flex items-center justify-between">
            <label className="block text-sm font-semibold text-textPrimary flex items-center gap-2">
              <Globe className="w-4 h-4 text-primary" />
              Academic Literature Sources
              <span className="text-xs font-normal text-textSecondary">(Zero API Keys Required)</span>
            </label>
            <button
              type="button"
              onClick={toggleAllSources}
              className="text-xs text-primary hover:text-primaryHover font-medium transition-colors"
            >
              {selectedSources.length === ACADEMIC_SOURCES.length ? 'Select Only arXiv' : 'Select All Sources'}
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {ACADEMIC_SOURCES.map((source) => {
              const isSelected = selectedSources.includes(source.id);
              return (
                <div
                  key={source.id}
                  onClick={() => toggleSource(source.id)}
                  className={`p-3.5 rounded-xl border transition-all duration-200 cursor-pointer flex items-start gap-3 select-none ${
                    isSelected
                      ? `bg-surface/90 ${source.borderActiveClass} shadow-md`
                      : 'bg-background/40 border-border opacity-70 hover:opacity-100 hover:border-border/80'
                  }`}
                >
                  <div
                    className={`mt-0.5 w-5 h-5 rounded-md flex items-center justify-center border transition-colors shrink-0 ${
                      isSelected
                        ? 'bg-primary border-primary text-white'
                        : 'border-border bg-surface'
                    }`}
                  >
                    {isSelected && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-sm text-white">{source.name}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full border ${source.badgeClass}`}>
                        {source.tag}
                      </span>
                    </div>
                    <p className="text-xs text-textSecondary leading-relaxed">
                      {source.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
          <p className="text-[11px] text-textSecondary">
            The Literature Agent will fetch papers exclusively from your checked sources and synthesize the cross-database findings.
          </p>
        </div>

        {/* References Upload */}
        <div>
          <label className="block text-sm font-medium mb-2 flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-primary" />
            Upload Reference Papers (Optional: PDF, DOCX, TXT)
          </label>
          <div className="border-2 border-dashed border-border rounded-lg p-7 text-center hover:bg-surface/50 transition-colors">
            <input 
              type="file" 
              multiple 
              accept=".pdf,.doc,.docx,.txt"
              onChange={(e) => setFiles(e.target.files)} 
              className="hidden" 
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
              <UploadCloud className="w-9 h-9 text-primary mb-2.5" />
              <span className="text-sm text-textSecondary">Click to browse papers</span>
              {files.length > 0 && (
                <div className="mt-3 text-sm text-white font-medium">
                  {files.length} document{files.length > 1 ? 's' : ''} selected
                </div>
              )}
            </label>
          </div>
        </div>

        <button 
          type="submit" 
          disabled={loading}
          className="btn-primary w-full py-3.5 flex justify-center items-center text-lg mt-4 font-semibold"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin mr-2" />
              Planning Research Mission...
            </>
          ) : (
            'Generate Task Plan & Search Literature'
          )}
        </button>
      </form>
    </div>
  );
}
