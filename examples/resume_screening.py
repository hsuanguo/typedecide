"""Evaluate a resume against several structured hiring-screen questions."""
from __future__ import annotations

import argparse
import json

import typedecide as td


RESUME = """SASHA BERNOULLI
San Francisco, CA | sasha.bernoulli@email.com | github.com/sashabernoulli | linkedin.com/in/sashabernoulli

PROFESSIONAL SUMMARY
Experienced Product Engineer building developer-focused tools and platforms. Expertise in full-stack development with deep specialization in frontend architecture and UI/UX for technical audiences. Proven track record of shipping products that increase developer productivity and improve developer experience.

EXPERIENCE

Senior Product Engineer | CloudSync Systems | San Francisco, CA | Jan 2022 - Present
- Led frontend architecture redesign for cloud orchestration dashboard, reducing initial load time by 65% and improving TypeScript coverage from 42% to 98%
- Designed and implemented real-time collaboration features using WebSockets and Operational Transformation for multi-developer workflows
- Built internal API gateway and request optimization layer (Node.js/Express) that reduced backend calls by 40%, improving dashboard responsiveness
- Mentored 3 junior engineers on frontend best practices and code quality standards
- Tech Stack: React, TypeScript, Redux, Node.js, PostgreSQL, AWS

Product Engineer | DevTools Lab | San Francisco, CA | May 2021 - Dec 2021
- Architected and launched IDE plugin marketplace with 50k+ downloads; designed Vue.js frontend with Electron integration
- Implemented backend services for plugin discovery, versioning, and analytics (Python/FastAPI) handling 2M+ monthly requests
- Optimized plugin installation pipeline, reducing time from 45s to 8s through lazy-loading and caching strategies
- Built comprehensive monitoring and error tracking for frontend and backend systems using Datadog and custom logging
- Tech Stack: Vue.js, Python, FastAPI, PostgreSQL, Redis, Docker

Software Engineer | Nexus Networks | San Francisco, CA | Jan 2021 - Apr 2021
- Developed interactive network topology visualization tool using D3.js and WebGL for rendering 10k+ nodes in real-time
- Created REST API endpoints for network state management and device configuration (Go/Gin framework)
- Implemented real-time data sync between frontend and backend using gRPC, reducing latency by 50%
- Contributed to SDK documentation and developer guides for third-party integrations
- Tech Stack: React, D3.js, Go, PostgreSQL, Kubernetes

Junior Software Engineer | CodePath Systems | San Francisco, CA | Jun 2020 - Jan 2021
- Built responsive web interfaces for code analysis tools using React and CSS-in-JS
- Developed backend microservices for code parsing and analysis (Java/Spring Boot)
- Optimized database queries reducing API response times by 30%
- Tech Stack: React, JavaScript, Java, Spring Boot, MySQL

SKILLS

Frontend: React, Vue.js, TypeScript, JavaScript (ES6+), HTML5, CSS3, D3.js, WebGL, Webpack, Tailwind CSS, Material-UI
Backend: Node.js, Python (FastAPI), Go, Java (Spring Boot), SQL (PostgreSQL, MySQL), Redis, MongoDB
Developer Tools: Git, Docker, Kubernetes, GitHub Actions, Datadog, New Relic
Specializations: Developer Experience, API Design, Real-time Systems, Performance Optimization, UI/UX for Technical Users

EDUCATION

B.S. Computer Science | University of California, Berkeley | 2019
Relevant Coursework: Data Structures, Algorithms, Systems Design, Databases, Web Development

CERTIFICATIONS & ACHIEVEMENTS
- AWS Certified Solutions Architect (Associate) - 2021
- Open Source Contributor: React Query (20+ merged PRs), Electron (5+ merged PRs)
- Speaker: "Building Developer-First UI" at React Conference 2022"""


QUESTIONS = (
    td.score(
        "years_of_experience",
        "How many years of professional experience does the candidate have as of September 15, 2026?",
        ["None", "2 years", "4 years", "6 years", "8 years", "10+ years"],
    ),
    td.score(
        "technical_depth",
        "Rate hands-on engineering depth using experience and project bullets: what the candidate personally built, "
        "how complex it was, and how much they owned. Ignore skills keyword lists, titles, and company names. "
        "Score depth shown rather than years worked. When torn between levels, pick the lower.",
        [
            "No roles or projects where they wrote code; exposure is adjacent only.",
            "Coding appears only as coursework, bootcamp, or tutorial projects; nothing shipped to real users.",
            "Small scoped work inside someone else's design, such as bug fixes or minor features.",
            "Owns features end to end in a live system across two layers with little supervision.",
            "Owns whole systems and architecture tradeoffs in two domains; solves hard problems with measurable impact and often mentors.",
            "Deep specialist with real breadth, such as widely used open-source maintenance, systems internals, or org-wide architecture at significant scale.",
        ],
    ),
    td.noul(
        "mentorship_demonstrated",
        "Does the resume demonstrate mentoring experience?",
        false="The resume does not describe mentoring or coaching others.",
        true="The resume describes mentoring, coaching, or developing other engineers.",
    ),
    td.noul(
        "llm_experience",
        "Does the candidate have experience developing LLM products?",
        false="The candidate does not show experience building AI or LLM products.",
        true="The candidate has built products or features powered by AI or large language models.",
    ),
    td.noul(
        "certifications_opensource",
        "Does the candidate have open-source experience?",
        false="The resume does not show open-source contributions or maintenance.",
        true="The resume shows open-source contributions, maintenance, or other substantive open-source work.",
    ),
    td.choice(
        "career_progression",
        "What type of career progression is shown?",
        {
            "steady_growth": "Clear progression with increasing seniority.",
            "lateral_moves": "Similar roles at different companies.",
            "job_hopping": "Frequent changes with short tenure.",
            "unclear": "The progression pattern is unclear.",
        },
    ),
    td.choice(
        "primary_talent_profile",
        "Pick the best match for the candidate's talent profile. Judge from experience holistically rather than titles or skills lists, and weight recent roles most heavily.",
        {
            "frontend_engineer": "Builds user-facing interfaces, design systems, browser performance, or accessibility; consumes APIs but does not own them.",
            "backend_engineer": "Builds server-side services, APIs, and data models; owns business logic, databases, queues, and service performance.",
            "full_stack_engineer": "Ships both UI and services on the same projects with neither side dominant.",
            "mobile_engineer": "Builds iOS, Android, or cross-platform apps with native SDKs or app-store releases.",
            "devops_infrastructure": "Owns CI/CD, Kubernetes, Terraform, cloud infrastructure, monitoring, reliability, or on-call.",
            "data_engineer": "Builds pipelines and data platforms such as ETL, warehouses, Spark, Airflow, dbt, or streaming.",
            "ml_ai_engineer": "Trains, fine-tunes, evaluates, or serves models, including applied ML and LLMs.",
            "security_engineer": "Focuses on application, cloud, or product security.",
            "embedded_systems": "Performs low-level firmware, driver, kernel, compiler, robotics, or hardware-constrained systems work.",
            "other": "Performs engineering work that fits none of the other profiles.",
        },
    ),
)


def main() -> None:
    """Score one resume against the hiring-screen questions and print the answers.

    The ``--backend`` flag selects any installed backend. The default is Jev.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=td.available_backends(), default="jev")
    args = parser.parse_args()

    backend = td.load(args.backend)
    try:
        response = backend.predict({"resume": RESUME}, QUESTIONS)
    finally:
        backend.close()

    questions_by_id = {question.id: question for question in QUESTIONS}
    print(json.dumps({
        question_id: {
            "selected": answer.selected,
            "selected_criterion": next(
                option.description
                for option in questions_by_id[question_id].criteria
                if option.id == answer.selected
            ),
            "probabilities": dict(zip(answer.option_ids, answer.probabilities)),
            "score": answer.score,
        }
        for question_id, answer in response.answers.items()
    }, indent=2))


if __name__ == "__main__":
    main()