import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, Loader2 } from 'lucide-react';
import api from '../services/api';

export default function ResearchInput() {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const [loading, setLoading] = useState(false);
  const [files, setFiles] = useState([]);
  const navigate = useNavigate();

  const onSubmit = async (data) => {
    setLoading(true);
    try {
      // Step 1: Submit Research Parameters and Upload Files
      const formData = new FormData();
      formData.append('research_question', data.research_question);
      if (data.goals) formData.append('goals', data.goals);
      if (data.constraints) formData.append('constraints', data.constraints);
      
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
        uploaded_files: uploadRes.data.uploaded_files
      };

      const supervisorRes = await api.post('/supervisor/tasks', supervisorPayload);
      
      // Step 3: Navigate to Task Board with state
      navigate('/tasks', { state: { workflow: supervisorRes.data } });
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
        <p className="text-textSecondary">Provide your objectives and files, and let the Supervisor Agent plan the work.</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="card space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">Research Question *</label>
          <textarea 
            {...register("research_question", { required: "This is required" })}
            className="input-field min-h-[100px]"
            placeholder="What is the core question you are trying to answer?"
          />
          {errors.research_question && <span className="text-red-400 text-sm mt-1">{errors.research_question.message}</span>}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium mb-2">Goals</label>
            <textarea 
              {...register("goals")}
              className="input-field min-h-[80px]"
              placeholder="E.g., Publish a paper, find market gaps..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Constraints</label>
            <textarea 
              {...register("constraints")}
              className="input-field min-h-[80px]"
              placeholder="E.g., Only use papers post-2020..."
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Upload References (PDF, DOCX, TXT)</label>
          <div className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:bg-surface/50 transition-colors">
            <input 
              type="file" 
              multiple 
              onChange={(e) => setFiles(e.target.files)} 
              className="hidden" 
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
              <UploadCloud className="w-10 h-10 text-primary mb-3" />
              <span className="text-sm text-textSecondary">Click to browse files</span>
              {files.length > 0 && (
                <div className="mt-4 text-sm text-white">
                  {files.length} file(s) selected
                </div>
              )}
            </label>
          </div>
        </div>

        <button 
          type="submit" 
          disabled={loading}
          className="btn-primary w-full py-3 flex justify-center items-center text-lg mt-4"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin mr-2" />
              Generating Task Plan...
            </>
          ) : (
            'Generate Task Plan'
          )}
        </button>
      </form>
    </div>
  );
}
