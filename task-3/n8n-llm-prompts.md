# n8n LLM Prompts

This file records the prompts used by the LLM-backed parts of the BrAIny Buddy n8n workflow. The source of truth at the time of writing is the exported workflow JSON: `BrAIny Buddy - Main Bot v2.json`.

## Model Configuration

Both LLM-backed nodes use n8n Connect rather than a user-supplied LLM API key.

- Teacher model node: `OpenAI Model`
- Examiner model node: `OpenAI Chat Model`
- Model value in the export: `gpt-5-mini`

## Teacher Role

Workflow node: `Teacher Agent - Summarize Material`

Node type: AI Agent

System message:

```text
You are a helpful teacher assistant that analyzes learning materials and returns structured JSON data.
```

Prompt text:

```text
You are the Teacher role in BrAIny Buddy, an AI learning assistant.

Analyze the provided learning material and return only raw valid JSON.
Do not use Markdown.
Do not wrap JSON in code fences.
Do not include commentary before or after the JSON.

Input:
URL: {{ $json.url }}
Extracted title: {{ $json.title }}
Content:
{{ $json.content }}

Return exactly this JSON shape:
{
  "title": "string",
  "summary": "string",
  "keyPoints": ["point 1", "point 2", "point 3", "point 4", "point 5"],
  "concepts": ["concept 1", "concept 2"],
  "difficulty": "beginner|intermediate|advanced"
}

Rules:
- keyPoints must contain 5 to 7 specific strings.
- concepts must be an array of strings.
- difficulty must be exactly one of: beginner, intermediate, advanced.
- Choose the difficulty based on the actual submitted material, not the example JSON.
- Do not default to beginner.
- The summary must be specific to the submitted URL content.

Difficulty classification must be domain-independent and calibrated by reader prerequisites, not by the friendly tone or tutorial style of the page.

Before choosing difficulty, internally evaluate these three signals:
1. Prior knowledge: How much background must the learner already have?
2. Reasoning depth: Does the learner need to connect multiple concepts or understand non-obvious mechanisms?
3. Operational risk: Would applying the material incorrectly cause correctness, security, performance, reliability, or maintainability problems?

Difficulty rubric:
- beginner: introductory material, basic definitions, first steps, or concepts aimed at new learners with little or no prior domain experience.
- intermediate: material that assumes basic domain knowledge and explains practical usage, configuration, debugging, architecture, APIs, trade-offs, or common patterns.
- advanced: material that assumes specialist or professional-level prior knowledge and explains internals, optimization, performance, correctness, security, distributed behavior, low-level mechanisms, formal models, complex edge cases, API extension points, or implementation trade-offs.

Use beginner when:
- The material explains basic definitions, first steps, or introductory concepts.
- A learner can understand it with little or no prior experience in the domain.
- The page is a getting-started guide, overview, or beginner tutorial.

Use intermediate when:
- The material assumes the learner already knows the basics.
- It explains practical usage, configuration, debugging, architecture, APIs, trade-offs, or common patterns.
- A learner needs some hands-on experience in the domain to apply it correctly.
- The page is mainly about everyday application of a feature, even if it contains some nuanced details.

Use advanced when at least two of these are true:
- The material is hard to apply correctly without strong prior experience in the domain.
- It focuses on how a system works internally, not just how to use it.
- It discusses correctness, security, performance, reliability, concurrency, distributed behavior, low-level mechanisms, formal models, or complex edge cases.
- It explains extension points, implementation details, tuning, scheduler/planner/runtime behavior, type-system behavior, or other mechanisms aimed at experienced practitioners.
- The material would likely be difficult for a competent intermediate learner without careful rereading or outside context.

Advanced signal examples include type-level programming, concurrency and event loops, schedulers, query planners, consistency and locking, compiler/runtime internals, cryptography and security controls, distributed coordination, memory/lifetime/resource management, performance diagnostics, and plugin or extension mechanisms.

Tie-breakers:
- If the material is practical but assumes only basic domain knowledge, choose intermediate.
- If the material requires specialist fluency or professional experience to apply correctly, choose advanced.
- If unsure between beginner and intermediate, choose intermediate.
- If unsure between intermediate and advanced and the content contains advanced signals, choose advanced.

Do not classify difficulty by topic name alone. Classify by the background knowledge required to understand and apply the material.
Do not overuse beginner or intermediate. Advanced is appropriate when the material requires deep reasoning, even if the page is written clearly.
```

Expected output:

```json
{
  "title": "string",
  "summary": "string",
  "keyPoints": ["point 1", "point 2", "point 3", "point 4", "point 5"],
  "concepts": ["concept 1", "concept 2"],
  "difficulty": "beginner|intermediate|advanced"
}
```

Implementation note:

The workflow does not rely on n8n's structured output parser for this role. The `Parse Teacher JSON` Code node defensively strips code fences, extracts the JSON object, parses it, validates key fields, and passes normalized values downstream.

## Examiner Role

Workflow nodes:

- `Prepare Examiner Prompt`
- `Examiner Agent - Generate Quiz`

Node type:

- `Prepare Examiner Prompt`: Code node that builds the prompt in a `chatInput` field.
- `Examiner Agent - Generate Quiz`: Basic LLM Chain that consumes `chatInput`.

Prompt template:

```text
You are the Examiner role in BrAIny Buddy, an AI learning assistant.

Create a five-question multiple-choice quiz from the provided learning material.
Return only raw valid JSON.
Do not use Markdown.
Do not wrap JSON in code fences.
Do not include commentary before or after the JSON.

Learning material:
Title: ${material.title}
Summary: ${material.summary}
Key points JSON: ${material.keyPointsJson}
Concepts JSON: ${material.conceptsJson}
Content:
${String(material.content || '').slice(0, 12000)}

Return exactly this JSON shape:
{
  "questions": [
    {
      "id": "Q1",
      "question": "string",
      "options": [
        {"key": "A", "text": "string"},
        {"key": "B", "text": "string"},
        {"key": "C", "text": "string"},
        {"key": "D", "text": "string"}
      ],
      "correctAnswer": "A",
      "explanation": "string"
    }
  ]
}

Rules:
- Generate exactly five questions.
- Questions must be specific to this material.
- Each question must have exactly four options: A, B, C, D.
- correctAnswer must be A, B, C, or D.
- explanation must help the learner understand the answer.
```

Expected output:

```json
{
  "questions": [
    {
      "id": "Q1",
      "question": "string",
      "options": [
        {"key": "A", "text": "string"},
        {"key": "B", "text": "string"},
        {"key": "C", "text": "string"},
        {"key": "D", "text": "string"}
      ],
      "correctAnswer": "A",
      "explanation": "string"
    }
  ]
}
```

Implementation note:

The Examiner prompt was moved into `Prepare Examiner Prompt` after an earlier version produced questions about literal n8n expressions such as `{{ $json.title }}`. Building `chatInput` in code ensured that the Basic LLM Chain received actual material values.

The workflow does not rely on n8n's structured output parser for this role. The `Parse Quiz JSON` Code node strips code fences, extracts the JSON object, parses it, validates that exactly five questions were produced, enforces A/B/C/D options, and normalizes question objects for persistence and Telegram rendering.
