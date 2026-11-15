# macOS App Toolkit

Design native macOS apps, in SwiftUI or AppKit, that look and behave like the Mac. Ships the
**macos-app-design** skill, the Mac counterpart of a web design skill: where a web page wants a
distinctive look, a Mac app looks great by matching Finder, Mail, Xcode and System Settings.

The skill is a copy of the canonical one in
[ihistand/claude-skills](https://github.com/ihistand/claude-skills/tree/main/macos-app-design),
synced by `scripts/sync-skills.sh`.

## Install

```
/plugin install macos-app-toolkit --marketplace ihistand/claude-plugins
```

## What it does

The skill triggers on its own when you design, restyle or polish a Mac window, screen, sheet,
inspector or Settings pane, or ask for an existing Mac screen to look better. It has the agent:

- name the closest system app and take its structure;
- pick the Mac's own containers (`Table`, `List`, grouped `Form`, `Grid`, `GroupBox`,
  `.inspector`, a `Settings` scene) in place of chips, shadowed cards, tinted lanes and hover lifts;
- keep colour for meaning, and make the screen behave like a Mac (selection, Return to open,
  context menus, menu-bar commands with shortcuts, undo);
- render it and look at the screenshot, in light and dark, before calling it done.

`references/behaviour.md` covers commands and menus, shortcuts and their clashes, context menus,
destructive and undoable actions, panels and focus, and the sandbox.

## Works well with

Xcode's own plugin (`/plugin install xcode@claude-plugins-official`, which needs an Xcode with agent support) adds
SwiftUI previews and Apple's `swiftui-specialist` and accessibility skills, which cover code
correctness. This skill covers how the app looks and behaves.
