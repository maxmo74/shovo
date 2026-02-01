# AGENTS.md - Operating Guidelines for Shovo Repository

This document outlines the operating guidelines and permissions for AI agents working within the Shovo web app repository.

## General Principles

1. **Repository Scope**: Agents may operate freely within the `/home/massimo/repos/shovo` directory and its subdirectories.

2. **Development Model**: **This application is entirely developed and tested by AI agents**. The user will only deploy to production and test in real-world scenarios. Agents are responsible for:
   - Writing all code
   - Testing all changes thoroughly before committing
   - Ensuring quality and correctness
   - No user intervention should be needed for development/testing

3. **Change Policy**: Agents should implement changes autonomously after understanding requirements. For significant architectural changes, discuss the approach first, but otherwise proceed with implementation and testing.

4. **Transparency**: Agents must always show diffs or summaries of proposed changes before making them.

5. **Deployment Workflow**: After completing any task, agents must ALWAYS:
   - Test changes thoroughly using available tools (mathematical verification, code analysis, etc.)
   - Update the patch version (no confirmation needed)
   - Commit all changes with a descriptive message (no confirmation needed)
   - Push changes to the remote repository (no confirmation needed)

   This ensures changes are immediately deployable by the user.

## Permissions and Restrictions

### Allowed Operations

1. **File Reading**: Full access to read any file within the repository
2. **File Modification**: May modify files within the repository with user approval
3. **Code Analysis**: Full access to analyze code structure and dependencies
4. **Testing**: May run tests and validation within the repository environment

### Restricted Operations

1. **External Changes**: No modifications to files outside the repository without explicit user permission
2. **System Configuration**: No changes to system-wide configurations or settings
3. **Network Operations**: Limited to repository-related network requests only
4. **Dependency Management**: May suggest but not automatically install new dependencies

## Workflow Guidelines

### Change Process

1. **Analysis Phase**: Agents should thoroughly analyze the current state before proposing changes
2. **Proposal Phase**: Present clear, detailed plans with expected outcomes
3. **Review Phase**: Show diffs and explain rationale for changes
4. **Execution Phase**: Implement changes only after explicit user approval
5. **Deployment Phase**: After task completion, AUTOMATICALLY (no confirmation needed):
   - **CRITICAL**: Update APP_VERSION in webapp/routes.py (increment patch version X.Y.Z → X.Y.Z+1)
   - Commit changes with descriptive message including version number
   - Push to remote repository for deployment

### Communication Protocol

1. **Status Updates**: Provide regular progress updates
2. **Error Reporting**: Immediately report any issues or unexpected behavior
3. **Completion Notification**: Clearly indicate when tasks are complete
4. **Version Tracking**: Document version changes and commit messages for transparency

### Version Management Process

**CRITICAL**: Always update the version after ANY code changes, bug fixes, or improvements.

1. **Patch Version Bump**: Edit webapp/routes.py and increment APP_VERSION (X.Y.Z → X.Y.Z+1) for ALL changes including:
   - Bug fixes
   - UI/UX improvements
   - Feature additions
   - Mobile optimizations
   - Any code modifications
2. **Commit Changes**: Create descriptive commit messages following conventional commits format, including the new version number
3. **Push Updates**: Push changes to remote repository after successful testing
4. **Documentation**: Update version references in documentation and changelogs when applicable

## Testing Guidelines

**CRITICAL**: Agents must thoroughly test all changes before committing. Testing methods include:

1. **Visual Browser Testing (REQUIRED for UI changes)**: Always use headless browser testing for UI/CSS changes
   - Install Playwright in a temp venv: `python3 -m venv /tmp/test_env && source /tmp/test_env/bin/activate && pip install playwright && playwright install chromium`
   - Create test HTML files in `/tmp` with the component being tested
   - Take screenshots at relevant breakpoints (375px, 480px, 360px for mobile)
   - Verify positioning, alignment, and visual appearance
   - Iterate until visually correct, THEN commit

2. **Mathematical/Logical Verification**: Analyze code logic, CSS positioning, etc. to verify correctness
   - This is supplementary, NOT a replacement for visual testing

3. **Code Analysis**: Review code paths, edge cases, and potential issues

4. **Test Documentation**: Create verification reports and screenshots in `/tmp` to document testing process

**IMPORTANT**: Never commit CSS/UI changes without visual browser verification. Mathematical analysis alone is insufficient - what looks correct in theory may not render correctly in practice.

### File Management During Testing

**IMPORTANT**: Never create test files or temporary artifacts in the git repository that will be committed.

**Rules**:
1. **Use `/tmp` for all test files**: Test HTML, verification reports, screenshots, etc. should go in `/tmp`
2. **Check `.gitignore`**: If a file must be in the repo temporarily, ensure it's in `.gitignore`
3. **Clean up**: Remove temporary test files after testing is complete
4. **Examples of files to keep out of repo**:
   - Test HTML pages
   - Verification reports
   - Screenshots
   - Temporary scripts
   - Debug output files

### Testing Mobile UI

For mobile UI changes:
1. Create test HTML files in `/tmp` to verify layouts
2. Use mathematical/geometric analysis to verify CSS positioning
3. Analyze responsive breakpoints and their interactions
4. Verify the CSS cascade at different viewport sizes

### CSS Positioning Best Practices

When working with absolute positioning in nested elements:

1. **Understanding the Box Model**: Always consider the full DOM hierarchy and padding/margins at each level
   - Parent padding affects where absolutely positioned children appear
   - To position an element at the edge of a grandparent, account for parent padding

2. **Negative Positioning Values**:
   - `right: -10px` moves an absolutely positioned element 10px to the RIGHT (outside parent)
   - `right: 10px` moves it 10px FROM the right edge (leftward)
   - Use negative values to extend elements beyond their parent container

3. **Vertical Centering**:
   - Use `top: 50%` + `transform: translateY(-50%)` for true vertical centering
   - This works regardless of element height or parent height

4. **Responsive Positioning**: When elements have different padding at different breakpoints, positioning offsets must be adjusted accordingly

### Known Mobile UI Issues

The following mobile UI issues have been identified through headless browser testing:

1. **Card Layout Gap**: Cards in the mobile version have a significant gap on the right side. The cards should extend closer to the edge with minimal padding.

2. **Mini-Poster Size**: The mini-poster thumbnail is very tiny and not proportionate. It should scale relative to the card height to be more visible and balanced.

3. **Search Box Size**: The search box is too small in mobile view. It should be larger, starting from the Watched tab and extending to just before the Trending fire button, making it more accessible for mobile users.

## Mobile UX/UI Focus Areas

For the current mobile optimization project, agents should prioritize:

1. **Responsive Design**: Ensure proper adaptation to all mobile screen sizes
2. **Touch Optimization**: Improve touch target sizes and gestures
3. **Performance**: Optimize for mobile network conditions
4. **Accessibility**: Enhance mobile accessibility features

## Version Control

1. **Commit Messages**: Use clear, descriptive commit messages
2. **Branch Strategy**: Create feature branches for significant changes
3. **Documentation**: Update documentation alongside code changes

## Emergency Procedures

1. **Rollback**: Be prepared to revert changes if issues arise
2. **Backup**: Ensure important files are backed up before major changes
3. **User Notification**: Immediately alert user to any critical issues

## Approval Requirements

All changes must be explicitly approved by the user before execution, with the following exceptions:
- Minor formatting fixes
- Documentation updates
- Read-only operations
- **Version bumps, git commits, and git pushes** (these should ALWAYS happen automatically after task completion)

**Important**: After completing any task, agents must automatically bump the patch version, commit changes, and push to remote WITHOUT asking for confirmation. This is required for deployment workflow.

Agents must always err on the side of caution and seek approval when in doubt, except for the deployment workflow steps listed above.