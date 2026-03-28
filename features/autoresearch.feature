Feature: autoresearch CLI
  As a researcher
  I want to use the autoresearch CLI
  So that I can manage research projects and execute deep research tasks

  Scenario: Initialize project directory
    Given the current directory has no .autoresearch folder
    When I run "autoresearch init"
    Then the .autoresearch directory should be created
    And the .autoresearch/state.json file should exist
    And the .autoresearch/tasks directory should exist
    And the .autoresearch/memory directory should exist
    And the .autoresearch/memory/sessions directory should exist

  Scenario: Initialize project detects Claude Code host
    Given the current directory has no .autoresearch folder
    And the directory has a ".claude" marker
    When I run "autoresearch init"
    Then the .autoresearch directory should be created
    And the .autoresearch/claude-code-skill.md file should exist
    And the output should contain "Detected host: claude_code"

  Scenario: Initialize project detects Cursor host
    Given the current directory has no .autoresearch folder
    And the directory has a ".cursorrules" marker
    When I run "autoresearch init"
    Then the .autoresearch directory should be created
    And the .autoresearch/cursor-skill.md file should exist
    And the output should contain "Detected host: cursor"

  Scenario: Initialize project detects OpenCode host
    Given the current directory has no .autoresearch folder
    And the directory has a ".opencode" marker
    When I run "autoresearch init"
    Then the .autoresearch directory should be created
    And the .autoresearch/opencode-skill.md file should exist
    And the output should contain "Detected host: opencode"

  Scenario: Validate configuration with valid config
    Given a valid autoresearch.yaml configuration file
    When I run "autoresearch validate"
    Then the command should succeed
    And the output should contain "Configuration is valid"

  Scenario: Validate configuration with SOD violation
    Given an autoresearch.yaml where synthesizer and fact-checker use the same model
    When I run "autoresearch validate"
    Then the command should fail
    And the output should contain "SOD violation"

  Scenario: Validate configuration with missing agent model
    Given an autoresearch.yaml with an enabled agent that has no model
    When I run "autoresearch validate"
    Then the command should fail
    And the output should contain "no model configured"

  Scenario: Run quick research
    Given the project is initialized
    When I run "autoresearch run 'AI agent architecture' --depth quick"
    Then a new task should be created in .autoresearch/tasks/
    And the task status should be DONE
    And the output directory should contain a report.md file

  Scenario: Run deep research
    Given the project is initialized
    When I run "autoresearch run 'multi-agent systems' --depth deep"
    Then a new task should be created in .autoresearch/tasks/
    And the task should pass through PLANNING, SEARCHING, READING, SYNTHESIZING, FACT_CHECKING states
    And the task status should be DONE
    And the output directory should contain a report.md file
    And the output directory should contain a sources.json file

  Scenario: Check task status
    Given a completed research task exists
    When I run "autoresearch status"
    Then the output should show the task status

  Scenario: Check specific task status
    Given a completed research task "task-2026-001" exists
    When I run "autoresearch status task-2026-001"
    Then the output should show the status of task "task-2026-001"

  Scenario: List research history
    Given multiple research tasks exist
    When I run "autoresearch list"
    Then the output should list all tasks

  Scenario: List last N tasks
    Given multiple research tasks exist
    When I run "autoresearch list --last 3"
    Then the output should list at most 3 tasks

  Scenario: JSON output mode
    Given the project is initialized
    When I run "autoresearch status --json"
    Then the output should be valid JSON
    And the JSON should contain a "tasks" field

  Scenario: Resume interrupted task
    Given a task in SEARCHING state
    When I run "autoresearch resume <task-id>"
    Then the task should continue from the SEARCHING phase

  Scenario: Revision on disputed claims
    Given the project is initialized
    And the fact-checker finds disputed claims
    When the deep research pipeline runs
    Then the task should enter REVISION state
    And after revision the task should return to FACT_CHECKING state
    And the final status should be DONE
