# Issue Writer Agent

Issue Writer Agent is a terminal-based assistant for turning rough software ideas into implementation-ready issues.

You start with an unfinished idea, such as "add passwordless login" or "ingest supplier registration data into the datalake". The agent uses an LLM to ask one clarifying question at a time, records your answers, preserves unknowns, then drafts a final specification in the format you choose and writes it to a new file in your configured output folder. If no output folder is configured, it uses your operating system temp directory.

The agent is prompted to act as a senior product owner throughout brainstorming and final specification: it focuses on user outcomes, business value, scope boundaries, prioritization, risks, measurable success, and acceptance criteria before turning the idea into implementation work.

The final output can be tuned for either:

- An AI coding agent that needs explicit implementation guidance.
- A human development team that benefits from rationale, tradeoffs, and collaboration notes.

## What It Does

The agent follows a structured workflow:

1. You invoke it from the terminal with a rough idea.
2. It asks one clarifying question.
3. You answer the question.
4. It asks the next most useful question.
5. You type `done`, `spec`, `generate`, or a similar stop phrase when the idea is defined enough.
6. It asks which output format you want.
7. It asks whether the issue is for an AI agent or a human team.
8. It asks whether the final specification should be rendered as Markdown or HTML.
9. It drafts the final issue/specification.
10. It writes the result to a new file in the configured output folder or operating system temp folder and prints the full file path.

The agent is designed for early product and engineering shaping work. It is useful when you know the direction of a feature or task but need help converting it into a clear, testable implementation brief.

## Supported Output Formats

The agent can generate:

- `github_issue`: A GitHub issue with sections such as summary, problem, proposed scope, acceptance criteria, implementation notes, and test notes.
- `user_story`: A user story with context, scope, acceptance criteria, assumptions, and implementation notes.
- `task`: An implementation task with objective, requirements, acceptance criteria, unknowns, and notes.

Acceptance criteria can be generated as regular checklist bullets or as Gherkin `Given/When/Then` scenarios.

## Supported Render Formats

The final specification can be rendered as:

- `markdown`: Markdown headings, bullets, and task-list checkboxes. This is the default and is written with a `.md` suffix.
- `html`: A complete semantic HTML document containing the issue specification. This is written with a `.html` suffix.

## Requirements

- Python 3.11 or newer.
- Access to an OpenAI-compatible chat completions API.
- A model endpoint reachable from your machine.

The agent has no third-party runtime dependencies. It uses Python standard library modules for config loading and HTTP calls.

## Installation

### 1. Clone Or Open The Project

Work from the project directory:

```bash
cd /path/to/issue-writer-agent
```

### 2. Install The Command

Install the package in editable mode:

```bash
python3 -m pip install -e .
```

After installation, the main command is:

```bash
issue_writer_agent
```

The package also provides a dashed alias:

```bash
issue-writer
```

If your environment has no network access and pip tries to download build dependencies, use:

```bash
python3 -m pip install -e . --no-build-isolation
```

### 3. Verify Installation

Run:

```bash
issue_writer_agent --help
```

Expected result:

```text
usage: issue_writer_agent [-h] [--config CONFIG] [--init-config | --configure]
                          [--config-path CONFIG_PATH]
                          [idea ...]
```

## Configuration

The agent reads configuration from TOML.

By default it checks these paths, in this order:

1. `./issue_writer_config.toml`
2. `~/.config/issue-writer-agent/config.toml`

You can also pass a config path explicitly:

```bash
issue_writer_agent --config ./issue_writer_config.toml "Add passwordless login"
```

### Guided First-Time Setup Or Config Changes

Run the interactive configuration onboarding whenever you want to create or change the config:

```bash
issue_writer_agent --configure
```

By default this creates or updates:

```text
./issue_writer_config.toml
```

The onboarding asks for:

- API key.
- OpenAI-compatible model URL.
- Model name.
- Default output format.
- Default implementer.
- Default render format.
- Output folder for generated specifications.
- Whether to use Gherkin acceptance criteria by default.

Press Enter to keep the value shown in brackets. Existing API keys are hidden; press Enter to keep the saved key, type a new key to replace it, or type `clear` to remove it.

To configure a different file:

```bash
issue_writer_agent --configure --config-path ~/.config/issue-writer-agent/config.toml
```

You can also use `--config` as the target path for onboarding:

```bash
issue_writer_agent --configure --config ./team-demo-config.toml
```

### Create A Starter Config Without Questions

Generate a starter config file:

```bash
issue_writer_agent --init-config
```

This creates a default TOML file without asking onboarding questions:

```text
./issue_writer_config.toml
```

The local config file is intentionally ignored by git through `.gitignore`, because it can contain API keys and personal model preferences.

### Example Config

```toml
api_key = ""
model_url = "https://api.x.ai/v1"
model_name = "grok-4.3"
default_output_format = "github_issue"
default_implementation_entity = "ai_agent"
default_render_format = "markdown"
output_folder = ""
gherkin_acceptance_criteria = false
```

Add your API key to `api_key` when using a hosted provider:

```toml
api_key = "your-api-key-here"
```

For local providers such as Ollama or LM Studio, `api_key` is often empty.

## Configuration Reference

### `api_key`

API key sent as a bearer token.

Default:

```toml
api_key = ""
```

Use an empty string for local endpoints that do not require authentication.

### `model_url`

Base URL for the OpenAI-compatible API.

The agent calls:

```text
{model_url}/chat/completions
```

Examples:

```toml
model_url = "https://api.openai.com/v1"
model_url = "https://api.x.ai/v1"
model_url = "http://localhost:11434/v1"
model_url = "http://localhost:1234/v1"
```

The trailing slash is optional.

### `model_name`

Model identifier sent to the API.

Examples:

```toml
model_name = "grok-4.3"
model_name = "gpt-4.1-mini"
model_name = "llama3.1"
model_name = "local-model"
```

The value must match the model name expected by your provider.

### `default_output_format`

Default final specification format.

Allowed values:

```toml
default_output_format = "github_issue"
default_output_format = "user_story"
default_output_format = "task"
```

When the agent asks for the output format, this value is preselected. Press Enter to accept it.

### `default_implementation_entity`

Default target implementer.

Allowed values:

```toml
default_implementation_entity = "ai_agent"
default_implementation_entity = "human_team"
```

Use `ai_agent` when the final issue should include more explicit technical discovery instructions, edge cases, tests, and constraints.

Use `human_team` when the final issue should leave more implementation flexibility and include more product rationale and collaboration notes.

### `default_render_format`

Default rendering format for the final specification.

Allowed values:

```toml
default_render_format = "markdown"
default_render_format = "html"
```

When the agent asks for the render format, this value is preselected. Press Enter to accept it.

### `output_folder`

Folder where generated specification files are written.

Default:

```toml
output_folder = ""
```

When empty or omitted, the agent writes generated specifications to the operating system temp folder.

Use a folder path to keep generated specifications in a predictable location:

```toml
output_folder = "/path/to/issue-writer-output"
```

The folder is created automatically when the agent writes a specification.

### `gherkin_acceptance_criteria`

Controls acceptance criteria style.

Default:

```toml
gherkin_acceptance_criteria = false
```

When false, acceptance criteria are generated as checklist bullets.

When true, acceptance criteria are generated in Gherkin style:

```text
Given ...
When ...
Then ...
```

## Environment Variable Overrides

Environment variables override TOML config values.

| Environment variable | Config key |
| --- | --- |
| `ISSUE_WRITER_API_KEY` | `api_key` |
| `OPENAI_API_KEY` | `api_key` |
| `ISSUE_WRITER_MODEL_URL` | `model_url` |
| `ISSUE_WRITER_MODEL_NAME` | `model_name` |
| `ISSUE_WRITER_DEFAULT_OUTPUT_FORMAT` | `default_output_format` |
| `ISSUE_WRITER_DEFAULT_IMPLEMENTATION_ENTITY` | `default_implementation_entity` |
| `ISSUE_WRITER_DEFAULT_RENDER_FORMAT` | `default_render_format` |
| `ISSUE_WRITER_OUTPUT_FOLDER` | `output_folder` |
| `ISSUE_WRITER_GHERKIN_ACCEPTANCE_CRITERIA` | `gherkin_acceptance_criteria` |

Example:

```bash
ISSUE_WRITER_MODEL_NAME="grok-4.3" issue_writer_agent "Improve checkout errors"
```

## Backend Examples

### xAI Grok

```toml
api_key = "your-xai-api-key"
model_url = "https://api.x.ai/v1"
model_name = "grok-4.3"
default_output_format = "github_issue"
default_implementation_entity = "ai_agent"
default_render_format = "markdown"
output_folder = ""
gherkin_acceptance_criteria = false
```

### OpenAI

```toml
api_key = "your-openai-api-key"
model_url = "https://api.openai.com/v1"
model_name = "gpt-4.1-mini"
default_output_format = "github_issue"
default_implementation_entity = "ai_agent"
default_render_format = "markdown"
output_folder = ""
gherkin_acceptance_criteria = false
```

### Ollama

Start Ollama separately, then configure:

```toml
api_key = ""
model_url = "http://localhost:11434/v1"
model_name = "llama3.1"
default_output_format = "github_issue"
default_implementation_entity = "ai_agent"
default_render_format = "markdown"
output_folder = ""
gherkin_acceptance_criteria = false
```

### LM Studio

Start the LM Studio local server, then configure:

```toml
api_key = ""
model_url = "http://localhost:1234/v1"
model_name = "local-model"
default_output_format = "github_issue"
default_implementation_entity = "ai_agent"
default_render_format = "markdown"
output_folder = ""
gherkin_acceptance_criteria = false
```

## Usage

### Basic Invocation

```bash
issue_writer_agent "Add passwordless login to my SaaS app"
```

### Invocation With Explicit Config

```bash
issue_writer_agent --config ./issue_writer_config.toml "Add passwordless login to my SaaS app"
```

### Interactive Idea Entry

If you do not pass an idea, the agent asks for one:

```bash
issue_writer_agent
```

### Stopping The Interview

During the interview, type one of these when you are ready to draft the specification:

```text
done
finish
generate
generate spec
spec
write spec
write the specification
draft issue
create issue
```

You do not need to answer every question perfectly. If something is unknown, say so. The final output will include it under unknowns and assumptions instead of pretending the answer is known.

The generated specification is not printed directly to the terminal. The agent writes it to a new file in the configured output folder, or to the operating system temp folder when `output_folder` is empty, and prints the full path, for example:

```text
Specification written to: <os-temp-dir>/issue-writer-abcd1234.md
```

## Terminal Flow

Questions are displayed on their own line with blank space before the answer prompt:

```text
What is the source format, delivery mechanism, and frequency of the registration data?

Answer: JDBC access to database, daily
```

When the agent is ready to draft, it asks for final choices:

```text
Output format [github_issue] (user_story, task, github_issue)

Selection:
Selected: github_issue

Render format [markdown] (markdown, html)

Selection:
Selected: markdown

Specification written to: <os-temp-dir>/issue-writer-abcd1234.md
```

Press Enter to accept the default shown in square brackets. The resolved value is printed after `Selected:` so the transcript is unambiguous.

## Configuration Onboarding Flow

Use onboarding for first-time setup or later changes:

```bash
issue_writer_agent --configure
```

Example interaction:

```text
Issue Writer Agent configuration
Creating config file: issue_writer_config.toml
Press Enter to keep the value shown in brackets.

API key [empty; press Enter to leave empty]

Value:
Selected: empty

Model URL (OpenAI-compatible base URL) [http://localhost:11434/v1]

Answer: https://api.x.ai/v1

Model name [llama3.1]

Answer: grok-4.3

Default output format [github_issue] (user_story, task, github_issue)

Selection:
Selected: github_issue

Default implementer [ai_agent] (ai_agent, human_team)

Selection:
Selected: ai_agent

Default render format [markdown] (markdown, html)

Selection:
Selected: markdown

Output folder [operating system temp folder; press Enter to use it]

Answer:
Selected: operating system temp folder

Use Gherkin acceptance criteria by default [no] (yes, no)

Selection:
Selected: no

Configuration written to: /path/to/issue-writer-agent/issue_writer_config.toml
```

## Fictitious Example 1: GitHub Issue For An AI Agent

Command:

```bash
issue_writer_agent "Ingest ACME vehicle registration data into the datalake"
```

Example interaction:

```text
Answer the questions one at a time. Type 'done' when you want the specification.

What is the source format, delivery mechanism, and frequency of the registration data?

Answer: JDBC access to an ACME database, daily

Which source tables or views contain the registration data?

Answer: registrations and model_variant tables, but I do not know their structure yet

Should ingestion be full snapshot or incremental?

Answer: Incremental based on a last_updated field

What should run the daily extraction and load?

Answer: Airflow

What is the target datalake format and cataloging approach?

Answer: Glue catalog tables backed by S3

What S3 path, partitioning columns, and merge keys should be used?

Answer: I don't know

What else should be clarified before drafting the specification?

Answer: done

Output format [github_issue] (user_story, task, github_issue)

Selection:
Selected: github_issue

Who will implement it [ai_agent] (ai_agent, human_team)

Selection:
Selected: ai_agent

Render format [markdown] (markdown, html)

Selection:
Selected: markdown

Specification written to: <os-temp-dir>/issue-writer-8x3p4k2m.md
```

Example generated file content excerpt:

```markdown
## Summary

Ingest ACME vehicle registration data from a JDBC-accessible source database into Glue catalog tables backed by S3.

## Proposed Scope

- Discover the schema for the `registrations` and `model_variant` source tables.
- Implement a daily Airflow-orchestrated incremental ingestion job.
- Use `last_updated` as the incremental cursor where available.
- Store JDBC credentials and connection parameters in AWS Secrets Manager.

## Acceptance Criteria

- [ ] The ingestion job reads ACME registration data through a read-only JDBC connection.
- [ ] The job loads new or changed records since the previous successful run.
- [ ] The loaded data is queryable through Glue catalog tables.
- [ ] Unknown S3 path, partitioning, and merge-key decisions are documented before production rollout.

## Unknowns And Assumptions

- Source table structure is not yet known.
- S3 path, partitioning columns, and merge keys are not yet defined.
```

## Fictitious Example 2: User Story For A Human Team

Command:

```bash
issue_writer_agent "Let account admins invite teammates by email"
```

Example interaction:

```text
Who should be able to invite teammates?

Answer: Account admins only

What should happen after an invite is sent?

Answer: The invited person receives an email with a link to join the account

Should invites expire?

Answer: Yes, after 7 days

Should admins be able to revoke pending invites?

Answer: Yes

Are there limits on the number of teammates per account?

Answer: I don't know

What else should be clarified before drafting the specification?

Answer: done

Output format [github_issue] (user_story, task, github_issue)

Selection: user_story
Selected: user_story

Who will implement it [ai_agent] (ai_agent, human_team)

Selection: human
Selected: human_team

Render format [markdown] (markdown, html)

Selection: html
Selected: html

Specification written to: <os-temp-dir>/issue-writer-z9q7w1af.html
```

Example generated file content excerpt:

```html
<!doctype html>
<html lang="en">
  <head>
    <title>Account admins can invite teammates by email</title>
  </head>
  <body>
    <h1>Account admins can invite teammates by email</h1>
    <section>
      <h2>User Story</h2>
      <p>As an account admin, I want to invite teammates by email so that I can bring my team into the account without manual support intervention.</p>
    </section>
    <section>
      <h2>Acceptance Criteria</h2>
      <ul>
        <li>Only account admins can create invitations.</li>
        <li>Invited users receive an email containing a join link.</li>
        <li>Invitation links expire after 7 days.</li>
        <li>Admins can revoke pending invitations.</li>
        <li>The team confirms whether account teammate limits apply before implementation is finalized.</li>
      </ul>
    </section>
  </body>
</html>
```

## Fictitious Example 3: Task With Gherkin Acceptance Criteria

Config:

```toml
default_output_format = "task"
default_implementation_entity = "ai_agent"
default_render_format = "markdown"
gherkin_acceptance_criteria = true
```

Command:

```bash
issue_writer_agent "Add CSV export to the monthly billing report"
```

Example interaction:

```text
Who should be able to export the report?

Answer: Finance admins

What columns should the CSV include?

Answer: Customer name, account ID, invoice number, invoice date, status, subtotal, tax, total

Should filters on the report page affect the export?

Answer: Yes, current filters should apply

Should the export be synchronous or emailed later?

Answer: Synchronous is fine for now

What else should be clarified before drafting the specification?

Answer: generate spec
```

Example generated file content excerpt:

```markdown
## Objective

Add a CSV export action to the monthly billing report for finance admins.

## Acceptance Criteria

Scenario: Finance admin exports the filtered billing report
Given a finance admin is viewing the monthly billing report
And the report has active filters
When the admin selects CSV export
Then the downloaded CSV contains only rows matching the active filters

Scenario: Export contains required billing columns
Given a finance admin exports the monthly billing report
When the CSV is generated
Then it includes customer name, account ID, invoice number, invoice date, status, subtotal, tax, and total
```

## Tips For Better Results

- Start with a concrete verb, such as "add", "ingest", "migrate", "validate", "export", or "notify".
- Give real constraints when you know them, such as platform, backend service, data source, user role, or deadline.
- Say "I don't know" when a detail is genuinely unknown.
- Stop the interview once the remaining questions are no longer improving the implementation brief.
- Use `ai_agent` when the output will be pasted into an autonomous coding agent.
- Use `human_team` when the output will be discussed, estimated, or refined by developers and product stakeholders.

## Troubleshooting

### `issue_writer_agent: command not found`

Install the package:

```bash
python3 -m pip install -e .
```

Then confirm the command exists:

```bash
issue_writer_agent --help
```

### `Configuration error: model_url cannot be empty`

Check `issue_writer_config.toml` and make sure `model_url` has a value.

### `Configuration error: default_output_format must be one of...`

Use one of:

```text
user_story
task
github_issue
```

### The Agent Cannot Reach The Model

Check:

- The model server is running.
- `model_url` points to the API base URL, not the UI URL.
- Hosted-provider API keys are present.
- Local providers expose an OpenAI-compatible `/v1/chat/completions` endpoint.

### The Model Gives Poor Or Vague Questions

Try:

- A stronger model.
- A more specific starting idea.
- More explicit answers during the interview.
- Stopping earlier and refining the generated issue manually.

## Development

Run the test suite:

```bash
python3 -m unittest discover -s tests
```

Run the package without installing:

```bash
python3 -m issue_writer_agent "Add audit logs for admin actions"
```

Check command metadata:

```bash
issue_writer_agent --help
```
