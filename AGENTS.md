# AGENTS.md - Operating Guidelines for Shovo Repository

This document outlines the operating guidelines and permissions for AI agents working within the Shovo web app repository.

## General Principles

1. **Repository Scope**: Agents may operate freely within the `/home/massimo/repos/shovo` directory and its subdirectories.

2. **Change Policy**: All changes must be reviewed and approved by the user before execution, except for minor formatting or documentation updates.

3. **Transparency**: Agents must always show diffs or summaries of proposed changes before making them.

4. **Deployment Workflow**: After completing any task, agents must ALWAYS:
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
   - Bump patch version in all relevant files
   - Commit changes with descriptive message
   - Push to remote repository for deployment

### Communication Protocol

1. **Status Updates**: Provide regular progress updates
2. **Error Reporting**: Immediately report any issues or unexpected behavior
3. **Completion Notification**: Clearly indicate when tasks are complete
4. **Version Tracking**: Document version changes and commit messages for transparency

### Version Management Process

1. **Patch Version Bump**: Increment patch version (X.Y.Z → X.Y.Z+1) for bug fixes and minor improvements
2. **Commit Changes**: Create descriptive commit messages following conventional commits format
3. **Push Updates**: Push changes to remote repository after successful testing
4. **Documentation**: Update version references in documentation and changelogs

## Testing with Headless Browser

Agents can now test their changes using the internal headless browser before deployment. This allows for visual verification of UI changes, especially for mobile layouts.

To test mobile UI:
1. Use Playwright or similar tools to capture screenshots at mobile viewport sizes
2. Review screenshots to verify layout, spacing, and component sizing
3. Test both portrait and landscape orientations if relevant

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