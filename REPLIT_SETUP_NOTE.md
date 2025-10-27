# Replit Setup Note

## Important: editor-in-chief.md File

The validation system requires the `editor-in-chief.md` file to be present in your Replit workspace root directory.

This file contains the quality scoring guidelines and is loaded by the validation prompts. Without it, you'll see warnings like:
```
⚠️ Warning: Could not load /home/runner/workspace/editor-in-chief.md
```

### To Fix This on Replit:

1. The `editor-in-chief.md` file exists in your local repository
2. Copy it to your Replit workspace root
3. This file is intentionally gitignored to keep it separate from the codebase
4. It contains your content quality standards and scoring rubric

The file should be placed at: `/home/runner/workspace/editor-in-chief.md`

Once this file is in place, Test 11 (Validation Prompt Loading) will load the proper scoring rules instead of defaulting to 0/25 scores.