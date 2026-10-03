# DevBridge

DevBridge connects people who have real-world problems with developers who can build solutions.

## Current phase: frontend only

The project is being built in phases. This phase contains only the React frontend, which uses local mock data.

```
DevBridge/
    frontend/       React + Vite (this phase)
    backend/        Express + Node + MongoDB (later)
    ai-service/     NLP + Deep Learning (later)
    networking/     Computer Networks work (later)
    coa/            COA work (later)
    devops/         Docker, Nginx, CI/CD (later)
    docs/           Documentation (later)
```

## Run the frontend

```
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

Other commands: `npm run build` (production build) and `npm run lint`.

Demo accounts:

| Email | Password | Role |
| --- | --- | --- |
| riya@devbridge.com | riya123 | user |
| arjun@devbridge.com | arjun123 | developer |

## Frontend structure

```
frontend/src/
    App.jsx           all app state, page switching and data-changing functions
    data/mockData.js  mock users and problems (same shape as the future MongoDB models)
    utils/helpers.js  small helper functions
    components/       Navbar, Footer, ProblemCard, SearchBar, ProblemForm, UpvoteButton,
                      CommentSection, SolutionCard, SolutionForm
    pages/            Home, Problems, ProblemDetails, SubmitProblem, EditProblem,
                      MyProblems, Login, Register, Profile
```

## Connecting the backend later

Pages and components never read the mock data directly. They receive data through props from `App.jsx`, and every change goes through a function in `App.jsx` (`addProblem`, `updateProblem`, `deleteProblem`, `toggleUpvote`, `addComment`, `addSolution`, `login`, `register`).

When the Express API is ready, only `App.jsx` needs to change: load `problems` from `GET /api/problems` instead of `mockProblems`, and make those functions call the matching API routes. The components stay the same.
