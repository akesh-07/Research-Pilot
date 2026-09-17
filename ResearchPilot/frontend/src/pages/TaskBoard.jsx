import { useLocation, Link } from 'react-router-dom';
import { ArrowLeft, Clock, ListChecks } from 'lucide-react';

export default function TaskBoard() {
  const location = useLocation();
  const workflow = location.state?.workflow;

  if (!workflow) {
    return (
      <div className="text-center py-20">
        <h2 className="text-2xl font-bold mb-4">No Active Workflow</h2>
        <p className="text-textSecondary mb-6">Start a new research mission to generate tasks.</p>
        <Link to="/" className="btn-primary">Go to Research Input</Link>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-4 mb-8">
        <Link to="/" className="p-2 hover:bg-surface rounded-lg transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold">{workflow.workflow_name}</h1>
          <p className="text-textSecondary text-sm flex items-center gap-2 mt-1">
            <ListChecks className="w-4 h-4" /> {workflow.agent_tasks.length} tasks generated
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {workflow.agent_tasks.map((taskItem, index) => (
          <div key={index} className="card flex flex-col h-full hover:border-primary/50 transition-colors">
            <div className="flex justify-between items-start mb-4">
              <span className="text-xs font-bold px-2 py-1 bg-surface border border-border rounded-md text-textSecondary">
                Step {index + 1}
              </span>
              <span className="text-xs font-bold px-2 py-1 rounded-md bg-primary/20 text-primary">
                {taskItem.agent}
              </span>
            </div>
            
            <p className="text-sm text-textSecondary flex-1 mb-4">{taskItem.task}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
