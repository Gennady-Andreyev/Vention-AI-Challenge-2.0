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
  "difficulty": "beginner"
}

Rules:
- keyPoints must contain 5 to 7 specific strings.
- concepts must be an array of strings.
- difficulty must be one of: beginner, intermediate, advanced.
- The summary must be specific to the submitted URL content.
```

Expected output:

```json
{
  "title": "string",
  "summary": "string",
  "keyPoints": ["point 1", "point 2", "point 3", "point 4", "point 5"],
  "concepts": ["concept 1", "concept 2"],
  "difficulty": "beginner"
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
