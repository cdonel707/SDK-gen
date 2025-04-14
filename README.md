# 🌿 Fern SDK Demo Bot

A web application that automates the setup of SDK demo environments for potential customers using Fern. It creates GitHub repositories, configures SDK generation, and produces working Python and TypeScript SDKs based on uploaded OpenAPI specifications.

## 🚀 Quick Start

1. Clone this repository
2. Set up environment variables:
   ```bash
   # Backend
   GITHUB_CLIENT_ID=your_github_client_id
   GITHUB_CLIENT_SECRET=your_github_client_secret
   GITHUB_ACCESS_TOKEN=your_github_access_token
   RAILWAY_STATIC_URL=your_railway_url
   ```

3. Install dependencies:
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt

   # Frontend
   cd frontend
   npm install
   ```

4. Run the development servers:
   ```bash
   # Backend (in backend directory)
   uvicorn main:app --reload

   # Frontend (in frontend directory)
   npm start
   ```

## 🛠️ Deployment to Railway

1. Create a new project on [Railway](https://railway.app)
2. Connect your GitHub repository
3. Add the following environment variables in Railway:
   - `GITHUB_CLIENT_ID`
   - `GITHUB_CLIENT_SECRET`
   - `GITHUB_ACCESS_TOKEN`
   - `RAILWAY_STATIC_URL` (will be provided by Railway)

4. Deploy! Railway will automatically build and deploy your application.

## 🔐 GitHub OAuth Setup

1. Go to GitHub Settings > Developer Settings > OAuth Apps
2. Create a new OAuth App with:
   - Homepage URL: Your Railway URL
   - Authorization callback URL: `https://your-railway-url/auth/callback`
3. Note down the Client ID and generate a Client Secret

## 📦 Project Structure

```
.
├── backend/
│   ├── main.py           # FastAPI application
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.js       # Main React component
│   │   ├── index.js     # React entry point
│   │   └── index.css    # Global styles
│   ├── package.json     # Node.js dependencies
│   └── tailwind.config.js
├── railway.toml         # Railway configuration
└── README.md
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.