import React, { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from './contexts/UserContext';

interface SavingsGoal {
  id: string;
  title: string;
  current_amount: number;
  target_amount: number;
  monthly_contribution: number;
  progress_percentage: number;
  remaining_amount: number;
  months_to_complete: number | null;
  is_completed: boolean;
}

interface UploadResponse {
  message: string;
  transactions_count: number;
  transactions: any[];
}

const GoalsPage: React.FC = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string>('');
  const { user, setUser } = useUser();
  const [isCreatingUser, setIsCreatingUser] = useState(false);
  const [username, setUsername] = useState('');
  const [savingsGoals, setSavingsGoals] = useState<SavingsGoal[]>([]);
  const [isLoadingGoals, setIsLoadingGoals] = useState(false);
  const [showCreateGoalModal, setShowCreateGoalModal] = useState(false);
  const [newGoal, setNewGoal] = useState({
    title: '',
    target_amount: '',
    monthly_contribution: ''
  });
  const [isCreatingGoal, setIsCreatingGoal] = useState(false);
  
  // Load goals from backend
  useEffect(() => {
    if (user) {
      loadGoals();
    }
  }, [user]);

  const loadGoals = async () => {
    if (!user) return;
    
    setIsLoadingGoals(true);
    try {
      const response = await fetch(`http://localhost:8000/users/${user.id}/goals`);
      if (response.ok) {
        const goals = await response.json();
        setSavingsGoals(goals);
      } else {
        console.error('Failed to load goals');
      }
    } catch (error) {
      console.error('Error loading goals:', error);
    } finally {
      setIsLoadingGoals(false);
    }
  };

  const createGoalHandler = async () => {
    if (!user || !newGoal.title || !newGoal.target_amount || !newGoal.monthly_contribution) {
      setUploadStatus('❌ Please fill in all goal fields');
      return;
    }

    setIsCreatingGoal(true);
    setUploadStatus('');

    try {
      const response = await fetch(`http://localhost:8000/users/${user.id}/goals`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: newGoal.title,
          target_amount: parseFloat(newGoal.target_amount),
          monthly_contribution: parseFloat(newGoal.monthly_contribution),
        }),
      });

      if (response.ok) {
        const createdGoal = await response.json();
        setSavingsGoals([...savingsGoals, createdGoal]);
        setUploadStatus(`✅ Goal "${createdGoal.title}" created successfully!`);
        setShowCreateGoalModal(false);
        setNewGoal({ title: '', target_amount: '', monthly_contribution: '' });
      } else {
        const errorData = await response.json();
        setUploadStatus(`❌ Failed to create goal: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      setUploadStatus('❌ Network error. Please check if backend is running.');
      console.error('Goal creation error:', error);
    } finally {
      setIsCreatingGoal(false);
    }
  };

  const getGoalIcon = (index: number) => {
    const icons = [
      "M218.83,103.77l-80-75.48a1.14,1.14,0,0,1-.11-.11,16,16,0,0,0-21.53,0l-.11.11L37.17,103.77A16,16,0,0,0,32,115.55V208a16,16,0,0,0,16,16H96a16,16,0,0,0,16-16V160h32v48a16,16,0,0,0,16,16h48a16,16,0,0,0,16-16V115.55A16,16,0,0,0,218.83,103.77ZM208,208H160V160a16,16,0,0,0-16-16H112a16,16,0,0,0-16,16v48H48V115.55l.11-.10L128,40l79.9,75.43.11.10Z",
      "M235.58,128.84,160,91.06V48a32,32,0,0,0-64,0V91.06L20.42,128.84A8,8,0,0,0,16,136v32a8,8,0,0,0,9.57,7.84L96,161.76v18.93L82.34,194.34A8,8,0,0,0,80,200v32a8,8,0,0,0,11,7.43l37-14.81,37,14.81A8,8,0,0,0,176,232V200a8,8,0,0,0-2.34-5.66L160,180.69V161.76l70.43,14.08A8,8,0,0,0,240,168V136A8,8,0,0,0,235.58,128.84ZM224,158.24l-70.43-14.08A8,8,0,0,0,144,152v32a8,8,0,0,0,2.34,5.66L160,203.31v16.87l-29-11.61a8,8,0,0,0-5.94,0L96,220.18V203.31l13.66-13.65A8,8,0,0,0,112,184V152a8,8,0,0,0-9.57-7.84L32,158.24v-17.3l75.58-37.78A8,8,0,0,0,112,96V48a16,16,0,0,1,32,0V96a8,8,0,0,0,4.42,7.16L224,140.94Z",
      "M208,40H48A16,16,0,0,0,32,56v58.77c0,89.61,75.82,119.34,91,124.39a15.53,15.53,0,0,0,10,0c15.2-5.05,91-34.78,91-124.39V56A16,16,0,0,0,208,40Zm0,74.79c0,78.42-66.35,104.62-80,109.18-13.53-4.51-80-30.69-80-109.18V56l160,0Z",
    ];
    return icons[index % icons.length];
  };

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const createUser = async () => {
    if (!username.trim()) {
      setUploadStatus('❌ Please enter a username first.');
      return;
    }

    setIsCreatingUser(true);
    setUploadStatus('');

    try {
      const response = await fetch('http://localhost:8000/users/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: username.trim() }),
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setUploadStatus(`✅ User created successfully! Welcome, ${userData.username}!`);
        setUsername(''); // Clear the input
        // Show goal creation modal after user is created
        setTimeout(() => {
          setShowCreateGoalModal(true);
          setUploadStatus('');
        }, 1500);
      } else {
        const errorData = await response.json();
        setUploadStatus(`❌ User creation failed: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      setUploadStatus('❌ Network error. Please check if backend is running.');
      console.error('User creation error:', error);
    } finally {
      setIsCreatingUser(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!user) {
      setUploadStatus('❌ Please create a user first before uploading statements.');
      return;
    }

    setIsUploading(true);
    setUploadStatus('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`http://localhost:8000/parser/upload-statement/${user.id}`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data: UploadResponse = await response.json();
        setUploadStatus(`✅ Successfully uploaded! ${data.transactions_count} transactions processed.`);
      } else {
        const errorData = await response.json();
        setUploadStatus(`❌ Upload failed: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      setUploadStatus('❌ Network error. Please check if backend is running.');
      console.error('Upload error:', error);
    } finally {
      setIsUploading(false);
      // Clear the input so the same file can be selected again
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900 p-4">
      {/* Mobile Phone Container */}
      <div className="relative flex h-[812px] w-full max-w-[375px] flex-col overflow-hidden rounded-[2.5rem] border-8 border-gray-800 dark:border-gray-700 shadow-2xl bg-gradient-to-br from-background-light-goals via-zaman-green/10 to-zaman-solar/5 dark:from-background-dark-goals dark:via-zaman-green/20 dark:to-zaman-green/5">
        {/* Notch */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-40 h-6 bg-gray-800 dark:bg-gray-700 rounded-b-2xl z-50"></div>
        
      <main className="flex-1 overflow-y-auto p-6 space-y-8 pt-8">
        <header className="flex items-center justify-between">
          <div className="w-7"></div>
          <h1 className="text-xl font-bold text-text-light dark:text-text-dark">My Goals</h1>
          {user && (
            <button 
              onClick={handleFileSelect}
              disabled={isUploading}
              className="bg-zaman-gradient p-2 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed text-gray-800 shadow-lg"
              title="Upload Bank Statement"
            >
              <svg fill="currentColor" height="20" viewBox="0 0 256 256" width="20" xmlns="http://www.w3.org/2000/svg">
                <path d="M224,144v64a8,8,0,0,1-8,8H40a8,8,0,0,1-8-8V144a8,8,0,0,1,16,0v56H208V144a8,8,0,0,1,16,0ZM93.66,77.66,120,51.31V144a8,8,0,0,0,16,0V51.31l26.34,26.35a8,8,0,0,0,11.32-11.32l-40-40a8,8,0,0,0-11.32,0l-40,40A8,8,0,0,0,93.66,77.66Z"/>
              </svg>
            </button>
          )}
          {!user && <div className="w-7"></div>}
        </header>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.csv,.txt"
          onChange={handleFileUpload}
          className="hidden"
        />

        {/* User Management Section */}
        {!user ? (
          <section className="bg-gradient-to-r from-surface-light to-zaman-green/5 dark:from-surface-dark dark:to-zaman-green/10 p-6 rounded-lg shadow-soft border border-zaman-green/20">
            <h2 className="text-lg font-bold text-text-light dark:text-text-dark mb-4">Welcome! Please create your account</h2>
            <div className="flex gap-3">
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                className="flex-1 px-3 py-2 border border-subtle-light dark:border-subtle-dark rounded-lg bg-background-light-goals dark:bg-background-dark-goals text-text-light dark:text-text-dark"
                onKeyPress={(e) => e.key === 'Enter' && createUser()}
              />
              <button
                onClick={createUser}
                disabled={isCreatingUser || !username.trim()}
                className="bg-zaman-gradient text-gray-800 px-4 py-2 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
              >
                {isCreatingUser ? 'Creating...' : 'Create User'}
              </button>
            </div>
          </section>
        ) : (
          <section className="bg-gradient-to-r from-surface-light to-zaman-green/5 dark:from-surface-dark dark:to-zaman-green/10 p-4 rounded-lg shadow-soft border border-zaman-green/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-subtle-light dark:text-subtle-dark">Logged in as</p>
                <p className="font-semibold text-text-light dark:text-text-dark">{user.username}</p>
                <p className="text-xs text-subtle-light dark:text-subtle-dark">ID: {user.id}</p>
              </div>
              <button
                onClick={() => setUser(null)}
                className="text-subtle-light dark:text-subtle-dark hover:text-text-light dark:hover:text-text-dark text-sm"
              >
                Switch User
              </button>
            </div>
          </section>
        )}

        {/* Upload status */}
        {uploadStatus && (
          <div className={`p-3 rounded-lg text-sm ${
            uploadStatus.includes('✅') 
              ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' 
              : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
          }`}>
            {uploadStatus}
          </div>
        )}

        {user && (
          <>
            <section>
              <h2 className="text-2xl font-bold text-text-light dark:text-text-dark mb-4">Savings Goals</h2>
          <div className="space-y-4">
            {isLoadingGoals ? (
              <div className="text-center py-8 text-subtle-light dark:text-subtle-dark">
                Loading your goals...
              </div>
            ) : savingsGoals.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-subtle-light dark:text-subtle-dark mb-4">You haven't created any goals yet</p>
                <button
                  onClick={() => setShowCreateGoalModal(true)}
                  className="px-6 py-3 bg-zaman-gradient text-gray-800 font-semibold rounded-lg shadow-md hover:shadow-lg transition-shadow"
                >
                  Create Your First Goal
                </button>
              </div>
            ) : (
              savingsGoals.map((goal, index) => (
                <div key={goal.id} className="bg-gradient-to-r from-surface-light to-zaman-green/10 dark:from-surface-dark dark:to-zaman-green/15 p-4 rounded-lg shadow-soft border border-zaman-green/10">
                  <div className="flex items-center gap-4">
                    <div className="bg-gradient-to-br from-zaman-green/20 to-zaman-solar/20 text-zaman-green p-3 rounded-full shrink-0 border border-zaman-green/10">
                      <svg fill="currentColor" height="24" viewBox="0 0 256 256" width="24" xmlns="http://www.w3.org/2000/svg">
                        <path d={getGoalIcon(index)}></path>
                      </svg>
                    </div>
                    <div className="flex-grow">
                      <div className="flex justify-between items-baseline mb-1">
                        <p className="font-semibold text-text-light dark:text-text-dark">{goal.title}</p>
                        <p className="text-sm font-medium text-text-light dark:text-text-dark">
                          ${goal.current_amount.toLocaleString()} / <span className="text-subtle-light dark:text-subtle-dark">${goal.target_amount.toLocaleString()}</span>
                        </p>
                      </div>
                      <div className="w-full bg-gradient-to-r from-background-light-goals to-zaman-solar/10 dark:from-background-dark-goals dark:to-zaman-green/10 rounded-full h-2.5 border border-zaman-green/5">
                        <div 
                          className="bg-zaman-gradient h-2.5 rounded-full shadow-sm" 
                          style={{ width: `${goal.progress_percentage}%` }}
                        ></div>
                      </div>
                      <div className="mt-2 text-xs text-subtle-light dark:text-subtle-dark flex justify-between">
                        <span>Monthly: ${goal.monthly_contribution.toLocaleString()}</span>
                        <span>{goal.months_to_complete} months remaining</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
            {savingsGoals.length > 0 && (
              <div className="mt-6 flex justify-center gap-2">
                <button
                  onClick={() => setShowCreateGoalModal(true)}
                  className="px-6 py-3 bg-zaman-gradient text-gray-800 font-semibold rounded-lg shadow-md hover:shadow-lg transition-shadow"
                >
                  + Add Goal
                </button>
              </div>
            )}
          </section>

          <section>
            <h2 className="text-2xl font-bold text-text-light dark:text-text-dark mb-4">Spending & Savings</h2>
          <div className="bg-gradient-to-r from-surface-light to-zaman-green/10 dark:from-surface-dark dark:to-zaman-green/15 p-4 rounded-lg shadow-soft space-y-4 border border-zaman-green/10">
            <div>
              <p className="text-sm text-subtle-light dark:text-subtle-dark">Spending Trend</p>
              <div className="flex items-baseline gap-2">
                <p className="text-3xl font-bold text-text-light dark:text-text-dark">$2,500</p>
                <p className="text-sm font-semibold text-negative-light dark:text-negative-dark">-12%</p>
              </div>
            </div>
            <div className="h-40 w-full">
              <svg fill="none" height="100%" preserveAspectRatio="none" viewBox="0 0 472 150" width="100%" xmlns="http://www.w3.org/2000/svg">
                <path d="M0 109C18.1538 109 18.1538 21 36.3077 21C54.4615 21 54.4615 41 72.6154 41C90.7692 41 90.7692 93 108.923 93C127.077 93 127.077 33 145.231 33C163.385 33 163.385 101 181.538 101C199.692 101 199.692 61 217.846 61C236 61 236 45 254.154 45C272.308 45 272.308 121 290.462 121C308.615 121 308.615 149 326.769 149C344.923 149 344.923 1 363.077 1C381.231 1 381.231 81 399.385 81C417.538 81 417.538 129 435.692 129C453.846 129 453.846 25 472 25" stroke="#2D9A86" strokeLinecap="round" strokeWidth="3"></path>
                <path d="M0 109C18.1538 109 18.1538 21 36.3077 21C54.4615 21 54.4615 41 72.6154 41C90.7692 41 90.7692 93 108.923 93C127.077 93 127.077 33 145.231 33C163.385 33 163.385 101 181.538 101C199.692 101 199.692 61 217.846 61C236 61 236 45 254.154 45C272.308 45 272.308 121 290.462 121C308.615 121 308.615 149 326.769 149C344.923 149 344.923 1 363.077 1C381.231 1 381.231 81 399.385 81C417.538 81 417.538 129 435.692 129C453.846 129 453.846 25 472 25V150H0V109Z" fill="url(#spending-gradient)"></path>
                <defs>
                  <linearGradient gradientUnits="userSpaceOnUse" id="spending-gradient" x1="236" x2="236" y1="1" y2="150">
                    <stop stopColor="#2D9A86" stopOpacity="0.3"></stop>
                    <stop offset="0.5" stopColor="#EEFE6D" stopOpacity="0.2"></stop>
                    <stop offset="1" stopColor="#2D9A86" stopOpacity="0.1"></stop>
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </div>
          
          <div className="bg-gradient-to-r from-surface-light to-zaman-green/10 dark:from-surface-dark dark:to-zaman-green/15 p-4 mt-4 rounded-lg shadow-soft space-y-4 border border-zaman-green/10">
            <div>
              <p className="text-sm text-subtle-light dark:text-subtle-dark">Savings Trend</p>
              <div className="flex items-baseline gap-2">
                <p className="text-3xl font-bold text-text-light dark:text-text-dark">$1,800</p>
                <p className="text-sm font-semibold text-positive-light dark:text-positive-dark">+8%</p>
              </div>
            </div>
            <div className="relative h-40 w-full flex items-center justify-center">
              <svg className="absolute" height="140" viewBox="0 0 36 36" width="140">
                <path 
                  className="stroke-current text-background-light-goals/50 dark:text-background-dark-goals/50" 
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                  fill="none" 
                  strokeWidth="4"
                ></path>
                <path 
                  className="stroke-current text-zaman-green" 
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                  fill="none" 
                  strokeDasharray="70, 100" 
                  strokeLinecap="round" 
                  strokeWidth="4"
                  style={{ filter: 'drop-shadow(0 2px 4px rgba(45, 154, 134, 0.3))' }}
                ></path>
              </svg>
              <div className="text-center">
                <p className="text-2xl font-bold text-text-light dark:text-text-dark">70%</p>
                <p className="text-sm text-subtle-light dark:text-subtle-dark">Saved</p>
              </div>
            </div>
          </div>
          </section>
          </>
        )}
      </main>

      {/* Goal Creation Modal */}
      {showCreateGoalModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-surface-light dark:bg-surface-dark rounded-2xl shadow-2xl max-w-md w-full p-6 border-2 border-zaman-green/20">
            <h3 className="text-2xl font-bold text-text-light dark:text-text-dark mb-4 text-center">
              Create New Goal 🎯
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-subtle-light dark:text-subtle-dark mb-2">
                  Goal Title
                </label>
                <input
                  type="text"
                  value={newGoal.title}
                  onChange={(e) => setNewGoal({ ...newGoal, title: e.target.value })}
                  placeholder="e.g. Dream Home, Vacation"
                  className="w-full px-4 py-3 rounded-lg bg-background-light-goals dark:bg-background-dark-goals border border-zaman-green/20 text-text-light dark:text-text-dark placeholder-subtle-light dark:placeholder-subtle-dark focus:outline-none focus:ring-2 focus:ring-zaman-green"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-subtle-light dark:text-subtle-dark mb-2">
                  Target Amount ($)
                </label>
                <input
                  type="number"
                  value={newGoal.target_amount}
                  onChange={(e) => setNewGoal({ ...newGoal, target_amount: e.target.value })}
                  placeholder="e.g. 15000"
                  className="w-full px-4 py-3 rounded-lg bg-background-light-goals dark:bg-background-dark-goals border border-zaman-green/20 text-text-light dark:text-text-dark placeholder-subtle-light dark:placeholder-subtle-dark focus:outline-none focus:ring-2 focus:ring-zaman-green"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-subtle-light dark:text-subtle-dark mb-2">
                  Monthly Contribution ($)
                </label>
                <input
                  type="number"
                  value={newGoal.monthly_contribution}
                  onChange={(e) => setNewGoal({ ...newGoal, monthly_contribution: e.target.value })}
                  placeholder="e.g. 500"
                  className="w-full px-4 py-3 rounded-lg bg-background-light-goals dark:bg-background-dark-goals border border-zaman-green/20 text-text-light dark:text-text-dark placeholder-subtle-light dark:placeholder-subtle-dark focus:outline-none focus:ring-2 focus:ring-zaman-green"
                />
              </div>

              {uploadStatus && (
                <p className="text-sm text-center text-text-light dark:text-text-dark">
                  {uploadStatus}
                </p>
              )}

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowCreateGoalModal(false);
                    setNewGoal({ title: '', target_amount: '', monthly_contribution: '' });
                    setUploadStatus('');
                  }}
                  className="flex-1 px-4 py-3 bg-surface-light dark:bg-surface-dark border-2 border-zaman-green/30 text-text-light dark:text-text-dark font-semibold rounded-lg hover:bg-zaman-green/10 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={createGoalHandler}
                  disabled={isCreatingGoal}
                  className="flex-1 px-4 py-3 bg-zaman-gradient text-gray-800 font-semibold rounded-lg shadow-md hover:shadow-lg transition-shadow disabled:opacity-50"
                >
                  {isCreatingGoal ? 'Creating...' : 'Create Goal'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <footer className="bg-surface-light/80 dark:bg-surface-dark/80 backdrop-blur-lg border-t border-zaman-green/10">
        <nav className="flex justify-center p-2 gap-4">
          <button 
            onClick={() => navigate('/chat')}
            className="flex flex-col items-center justify-center gap-1 p-2 rounded-lg text-subtle-light dark:text-subtle-dark w-24"
          >
            <svg fill="currentColor" height="24" viewBox="0 0 256 256" width="24" xmlns="http://www.w3.org/2000/svg">
              <path d="M216,80H184V48a16,16,0,0,0-16-16H40A16,16,0,0,0,24,48V176a8,8,0,0,0,13,6.22L72,154V184a16,16,0,0,0,16,16h93.59L219,230.22a8,8,0,0,0,5,1.78,8,8,0,0,0,8-8V96A16,16,0,0,0,216,80ZM66.55,137.78,40,159.25V48H168v88H71.58A8,8,0,0,0,66.55,137.78ZM216,207.25l-26.55-21.47a8,8,0,0,0-5-1.78H88V152h80a16,16,0,0,0,16-16V96h32Z"></path>
            </svg>
            <span className="text-xs font-medium">Chat</span>
          </button>
          <button className="flex flex-col items-center justify-center gap-1 p-2 rounded-lg bg-zaman-gradient text-gray-800 w-24 shadow-lg">
            <svg fill="currentColor" height="24" viewBox="0 0 256 256" width="24" xmlns="http://www.w3.org/2000/svg">
              <path d="M232,64H208V56a16,16,0,0,0-16-16H64A16,16,0,0,0,48,56v8H24A16,16,0,0,0,8,80V96a40,40,0,0,0,40,40h3.65A80.13,80.13,0,0,0,120,191.61V216H96a8,8,0,0,0,0,16h64a8,8,0,0,0,0-16H136V191.58c31.94-3.23,58.44-25.64,68.08-55.58H208a40,40,0,0,0,40-40V80A16,16,0,0,0,232,64ZM48,120A24,24,0,0,1,24,96V80H48v32q0,4,.39,8ZM232,96a24,24,0,0,1-24,24h-.5a81.81,81.81,0,0,0,.5-8.9V80h24Z"></path>
            </svg>
            <span className="text-xs font-bold">Goals</span>
          </button>
        </nav>
      </footer>
      </div>
    </div>
  );
};

export default GoalsPage;