import { useLocation, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { ArrowLeft, ListChecks, Play, CheckCircle2, Clock, Loader2, BookOpen } from 'lucide-react';
import api from '../services/api';

export default function TaskBoard() {
  const location = useLocation();
  const initialWorkflow = location.state?.workflow;
  const researchContext = location.state?.researchContext;
  
  const [tasks, setTasks] = useState([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [literatureResults, setLiteratureResults] = useState(null);

  useEffect(() => {
    if (initialWorkflow) {
      setTasks(initialWorkflow.agent_tasks.map((t, idx) => ({
        ...t,
        id: `task-${idx}`,
        status: 'pending', // 'pending', 'in-progress', 'completed'
        step: idx + 1
      })));
    }
  }, [initialWorkflow]);

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
        setLiteratureResults(response.data.summaries);
        
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

      {literatureResults && (
        <div className="mb-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-primary" />
            Literature Analysis Results
          </h2>
          {literatureResults.length === 0 ? (
            <div className="card bg-surface/50 border border-border text-center py-10">
              <p className="text-textSecondary">No literature files were uploaded for this research mission.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6">
              {literatureResults.map((result, idx) => (
                <div key={idx} className="card bg-surface/50 border border-primary/20 relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-primary to-purple-500" />
                  <h3 className="text-xl font-bold mb-4 ml-2">{result.filename}</h3>
                  
                  <div className="mb-6 ml-2">
                    <h4 className="text-sm font-bold text-textSecondary uppercase tracking-wider mb-2">Summary</h4>
                    <p className="text-white leading-relaxed bg-background/50 p-4 rounded-lg border border-border">
                      {result.summary}
                    </p>
                  </div>
                  
                  <div className="ml-2">
                    <h4 className="text-sm font-bold text-textSecondary uppercase tracking-wider mb-2">Key Points</h4>
                    <ul className="space-y-3">
                      {result.important_points.map((point, i) => (
                        <li key={i} className="flex items-start gap-3 bg-background/50 p-3 rounded-lg border border-border">
                          <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                          <span className="text-white">{point}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
