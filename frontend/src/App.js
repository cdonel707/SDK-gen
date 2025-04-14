import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [companyName, setCompanyName] = useState('');
  const [openApiSpec, setOpenApiSpec] = useState(null);
  const [languages, setLanguages] = useState(['python', 'typescript']);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setOpenApiSpec(e.target.result);
      };
      reader.readAsText(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post('/setup', {
        company_name: companyName,
        openapi_spec: openApiSpec,
        languages: languages
      });
      setResult(response.data);
    } catch (error) {
      console.error('Error:', error);
      alert('An error occurred while setting up the SDKs');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-6 flex flex-col justify-center sm:py-12">
      <div className="relative py-3 sm:max-w-xl sm:mx-auto">
        <div className="relative px-4 py-10 bg-white shadow-lg sm:rounded-3xl sm:p-20">
          <div className="max-w-md mx-auto">
            <div className="divide-y divide-gray-200">
              <div className="py-8 text-base leading-6 space-y-4 text-gray-700 sm:text-lg sm:leading-7">
                <h1 className="text-2xl font-bold mb-8">🌿 Fern SDK Demo Bot</h1>
                
                {!result ? (
                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Company Name</label>
                      <input
                        type="text"
                        value={companyName}
                        onChange={(e) => setCompanyName(e.target.value)}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">OpenAPI Specification</label>
                      <input
                        type="file"
                        onChange={handleFileUpload}
                        className="mt-1 block w-full"
                        accept=".yaml,.yml,.json"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">Languages</label>
                      <div className="mt-2 space-y-2">
                        {['python', 'typescript'].map((lang) => (
                          <label key={lang} className="inline-flex items-center">
                            <input
                              type="checkbox"
                              checked={languages.includes(lang)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setLanguages([...languages, lang]);
                                } else {
                                  setLanguages(languages.filter(l => l !== lang));
                                }
                              }}
                              className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            />
                            <span className="ml-2">{lang.charAt(0).toUpperCase() + lang.slice(1)}</span>
                          </label>
                        ))}
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={loading}
                      className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      {loading ? 'Setting up...' : 'Setup SDKs'}
                    </button>
                  </form>
                ) : (
                  <div className="space-y-4">
                    <h2 className="text-xl font-semibold">🎉 Setup Complete!</h2>
                    <div className="space-y-2">
                      <p>Configuration Repository: <a href={result.repos.config} className="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">{result.repos.config}</a></p>
                      {Object.entries(result.repos.sdks).map(([lang, url]) => (
                        <p key={lang}>
                          {lang.charAt(0).toUpperCase() + lang.slice(1)} SDK: <a href={url} className="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">{url}</a>
                        </p>
                      ))}
                    </div>
                    <button
                      onClick={() => setResult(null)}
                      className="mt-4 w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      Start Over
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App; 