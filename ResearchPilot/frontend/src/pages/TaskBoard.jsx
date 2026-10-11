import { useLocation, Link } from 'react-router-dom';
import { useState } from 'react';
import { 
  ArrowLeft, 
  ListChecks, 
  Play, 
  CheckCircle2, 
  Clock, 
  Loader2, 
  BookOpen, 
  ExternalLink, 
  Sparkles, 
  FileText, 
  Globe, 
  Calendar, 
  Users 
} from 'lucide-react';
import api from '../services/api';

export default function TaskBoard() {
  const location = useLocation();
  const initialWorkflow = location.state?.workflow;
  const researchContext = location.state?.researchContext;
  
  const [tasks, setTasks] = useState(() => {
    if (!initialWorkflow?.agent_tasks) return [];
    return initialWorkflow.agent_tasks.map((t, idx) => ({
      ...t,
      id: `task-${idx}`,
      status: 'pending', // 'pending', 'in-progress', 'completed'
      step: idx + 1
    }));
  });
  const [isExecuting, setIsExecuting] = useState(false);
  const [literatureResults, setLiteratureResults] = useState(null);

  if (!initialWorkflow) {
    return (
      <div className="text-center py-20">
        <h2 className="text-2xl font-bold mb-4">No Active Workflow</h2>
        <p className="text-textSecondary mb-6">Start a new research mission to generate tasks.</p>
        <Link to="/" className="btn-primary">Go to Research Input</Link>
      </div>
    );
  }

  const startResearch = async () => {
    setIsExecuting(true);
    
    // Find literature task
    const litTaskIndex = tasks.findIndex(t => t.agent === "Literature Search Agent" || t.agent.includes("Literature"));
    
    if (litTaskIndex !== -1) {
      // Mark as in-progress
      setTasks(prev => prev.map((t, i) => i === litTaskIndex ? { ...t, status: 'in-progress' } : t));
      
      try {
        const response = await api.post('/literature/summarize', researchContext);
        setLiteratureResults(response.data);
        
        // Mark as completed
        setTasks(prev => prev.map((t, i) => i === litTaskIndex ? { ...t, status: 'completed' } : t));
      } catch (error) {
        console.error("Literature Agent failed:", error);
        alert("Failed to execute Literature Agent.");
        setTasks(prev => prev.map((t, i) => i === litTaskIndex ? { ...t, status: 'pending' } : t));
      }
    }
    
    // For now we stop after Literature Agent
    setIsExecuting(false);
  };

  // Helper getters to handle both new schema and legacy array formats
  const uploadedPapers = literatureResults?.uploaded_summaries || 
    (Array.isArray(literatureResults?.summaries) 
      ? literatureResults.summaries.filter(p => p.source_type === 'uploaded') 
      : (Array.isArray(literatureResults) ? literatureResults.filter(p => p.source_type !== 'web_discovered') : []));

  const discoveredPapers = literatureResults?.discovered_papers || 
    (Array.isArray(literatureResults?.summaries) 
      ? literatureResults.summaries.filter(p => p.source_type === 'web_discovered') 
      : (Array.isArray(literatureResults) ? literatureResults.filter(p => p.source_type === 'web_discovered') : []));

  const synthesis = literatureResults?.synthesis || "";
  const hasResults = uploadedPapers.length > 0 || discoveredPapers.length > 0 || !!synthesis;

  return (
    <div className="max-w-[1200px] mx-auto w-full">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div className="flex items-center gap-4">
          <Link to="/" className="p-2 hover:bg-surface rounded-lg transition-colors border border-transparent hover:border-border">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400">
              {initialWorkflow.workflow_name}
            </h1>
            <p className="text-textSecondary text-sm flex items-center gap-2 mt-1">
              <ListChecks className="w-4 h-4" /> {initialWorkflow.agent_tasks.length} tasks in pipeline
            </p>
          </div>
        </div>
        
        <button 
          onClick={startResearch} 
          disabled={isExecuting || tasks.every(t => t.status === 'completed')}
          className="btn-primary flex items-center gap-2 py-3 px-6 text-lg font-bold shadow-lg shadow-primary/20"
        >
          {isExecuting ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5 fill-current" />}
          {isExecuting ? "Executing Pipeline..." : "Start Research"}
        </button>
      </div>

      {/* Task Pipeline List */}
      <div className="grid grid-cols-1 gap-4 mb-12">
        {tasks.map((taskItem) => (
          <div 
            key={taskItem.id} 
            className={`card flex items-start gap-4 transition-all duration-300 border-2 ${
              taskItem.status === 'in-progress' ? 'border-blue-500 shadow-lg shadow-blue-500/10' : 
              taskItem.status === 'completed' ? 'border-green-500/30' : 'border-border'
            }`}
          >
            <div className="mt-1">
              {taskItem.status === 'completed' && <CheckCircle2 className="w-6 h-6 text-green-400" />}
              {taskItem.status === 'in-progress' && <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />}
              {taskItem.status === 'pending' && <Clock className="w-6 h-6 text-textSecondary" />}
            </div>
            
            <div className="flex-1">
              <div className="flex justify-between items-start mb-2">
                <span className="text-sm font-bold px-3 py-1 rounded-md bg-primary/20 text-primary">
                  {taskItem.agent}
                </span>
                <span className="text-xs font-bold text-textSecondary">
                  Step {taskItem.step}
                </span>
              </div>
              <p className="text-textSecondary">{taskItem.task}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Literature Agent Results Section */}
      {literatureResults && (
        <div className="mb-12 animate-in fade-in slide-in-from-bottom-4 duration-700 space-y-8">
          <div className="flex items-center justify-between border-b border-border pb-4">
            <h2 className="text-2xl font-bold flex items-center gap-3">
              <BookOpen className="w-7 h-7 text-primary" />
              Literature Analysis & Research Synthesis
            </h2>
            <span className="text-xs px-3 py-1 bg-surface border border-border text-textSecondary rounded-full">
              {uploadedPapers.length} Uploaded • {discoveredPapers.length} Discovered on Web
            </span>
          </div>

          {!hasResults ? (
            <div className="card bg-surface/50 border border-border text-center py-10">
              <p className="text-textSecondary">No literature was retrieved or analyzed for this query.</p>
            </div>
          ) : (
            <>
              {/* Synthesis & Scientific Landscape Card */}
              {synthesis && (
                <div className="card bg-gradient-to-br from-surface to-surface/80 border border-primary/40 relative overflow-hidden shadow-xl shadow-primary/5">
                  <div className="absolute top-0 left-0 w-1.5 h-full bg-gradient-to-b from-primary via-purple-500 to-indigo-500" />
                  <div className="ml-2">
                    <div className="flex items-center gap-2 text-primary font-bold text-sm uppercase tracking-wider mb-2">
                      <Sparkles className="w-4 h-4" />
                      Scientific Landscape & Synthesis
                    </div>
                    <p className="text-textPrimary text-base leading-relaxed bg-background/60 p-5 rounded-lg border border-border/80">
                      {synthesis}
                    </p>
                  </div>
                </div>
              )}

              {/* Uploaded Papers Section */}
              {uploadedPapers.length > 0 && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-emerald-400" />
                    <h3 className="text-xl font-bold text-textPrimary">Uploaded Research Papers</h3>
                    <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      {uploadedPapers.length} Document{uploadedPapers.length > 1 ? 's' : ''}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 gap-6">
                    {uploadedPapers.map((result, idx) => (
                      <div key={idx} className="card bg-surface/60 border border-emerald-500/20 relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500" />
                        <div className="ml-2">
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="text-lg font-bold text-white">{result.title || result.filename}</h4>
                            <span className="text-xs px-2.5 py-1 rounded-md bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-medium">
                              Uploaded File
                            </span>
                          </div>

                          <div className="mb-4">
                            <span className="text-xs font-bold text-textSecondary uppercase tracking-wider block mb-1">Summary</span>
                            <p className="text-textPrimary text-sm leading-relaxed bg-background/50 p-4 rounded-lg border border-border">
                              {result.summary}
                            </p>
                          </div>

                          {result.important_points?.length > 0 && (
                            <div>
                              <span className="text-xs font-bold text-textSecondary uppercase tracking-wider block mb-2">Key Extracted Points</span>
                              <ul className="space-y-2">
                                {result.important_points.map((point, i) => (
                                  <li key={i} className="flex items-start gap-2.5 bg-background/40 p-3 rounded-lg border border-border/60 text-sm">
                                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                                    <span className="text-textPrimary">{point}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Web Discovered Papers Section (arXiv) */}
              {discoveredPapers.length > 0 && (
                <div className="space-y-4 pt-4">
                  <div className="flex items-center gap-2">
                    <Globe className="w-5 h-5 text-purple-400" />
                    <h3 className="text-xl font-bold text-textPrimary">Discovered Scientific Papers (arXiv)</h3>
                    <span className="text-xs px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                      {discoveredPapers.length} Retrieved from Web
                    </span>
                  </div>

                  <div className="grid grid-cols-1 gap-6">
                    {discoveredPapers.map((paper, idx) => (
                      <div key={idx} className="card bg-surface/60 border border-primary/30 relative overflow-hidden hover:border-primary/60 transition-all duration-300">
                        <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-primary to-purple-500" />
                        <div className="ml-2">
                          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-3">
                            <h4 className="text-lg font-bold text-white leading-snug">{paper.title || paper.filename}</h4>
                            <div className="flex items-center gap-2 shrink-0">
                              <span className="text-xs px-2.5 py-1 rounded-md bg-primary/20 text-primary border border-primary/30 font-medium">
                                arXiv Verified
                              </span>
                              {(paper.url || paper.pdf_url) && (
                                <a 
                                  href={paper.url || paper.pdf_url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="flex items-center gap-1.5 text-xs px-3 py-1 rounded-md bg-surface hover:bg-background border border-border hover:border-primary text-primary transition-colors font-semibold"
                                >
                                  Read Paper <ExternalLink className="w-3.5 h-3.5" />
                                </a>
                              )}
                            </div>
                          </div>

                          {/* Paper Metadata: Authors & Year */}
                          <div className="flex flex-wrap items-center gap-4 text-xs text-textSecondary mb-4">
                            {paper.authors?.length > 0 && (
                              <span className="flex items-center gap-1.5 bg-background/60 px-2.5 py-1 rounded border border-border/60">
                                <Users className="w-3.5 h-3.5 text-primary" />
                                {paper.authors.join(', ')}
                              </span>
                            )}
                            {paper.year && (
                              <span className="flex items-center gap-1.5 bg-background/60 px-2.5 py-1 rounded border border-border/60">
                                <Calendar className="w-3.5 h-3.5 text-primary" />
                                {paper.year}
                              </span>
                            )}
                          </div>

                          <div className="mb-4">
                            <span className="text-xs font-bold text-textSecondary uppercase tracking-wider block mb-1">
                              Relevance & Summary
                            </span>
                            <p className="text-textPrimary text-sm leading-relaxed bg-background/50 p-4 rounded-lg border border-border">
                              {paper.summary}
                            </p>
                          </div>

                          {paper.important_points?.length > 0 && (
                            <div>
                              <span className="text-xs font-bold text-textSecondary uppercase tracking-wider block mb-2">
                                Key Contributions & Findings
                              </span>
                              <ul className="space-y-2">
                                {paper.important_points.map((point, i) => (
                                  <li key={i} className="flex items-start gap-2.5 bg-background/40 p-3 rounded-lg border border-border/60 text-sm">
                                    <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                                    <span className="text-textPrimary">{point}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
