---
name: moodle-mbz-to-yaml
description: Extract and transform a Moodle .mbz export into YAML format. Use this skill whenever the user wants to convert a Moodle backup file (.mbz) or extracted Moodle export into a YAML exam file. This handles decompression, quiz selection, and conversion. Trigger when user mentions ".mbz", "moodle export", "moodle backup", or wants to convert moodle quiz data to yaml.
---

# Moodle MBZ to YAML Converter

Extract exam data from a Moodle backup file (.mbz) and convert it to the unified YAML format.

## Input Handling

**Accept two input types:**
1. **Compressed .mbz file** - Moodle backup archive
2. **Extracted folder** - Already decompressed Moodle export

### Decompressing .mbz Files

If the user provides a .mbz file:

1. Create a temporary directory for extraction, for example :
   ```bash
   mkdir -p ./tmp_moodle_extract
   ```

2. Extract using tar:
   ```bash
   tar -xvzf "<path_to_mbz>" -C ./tmp_moodle_extract
   ```

3. Track the temp directory path to clean up later

4. When done (after YAML is generated), remove the temp directory:
   ```bash
   rm -rf ./tmp_moodle_extract
   ```

## Finding Quiz Files

The quiz.xml files are located at:
```
<extracted_folder>/activities/quiz_<id>/quiz.xml
```

To find all quizzes:

1. List all quiz directories:
   ```bash
   ls <extracted_folder>/activities/ | grep quiz_
   ```

2. If multiple quizzes exist, extract metadata from each:
   - Read the `quiz.xml` file
   - Extract: quiz name (from `<name>` tag), date (from `<timeopen>` timestamp)
   - Present options to user with quiz names and dates

3. **Ask user which quiz(es) to export.** If multiple selected, use a todo list to track progress for each quiz.

## Finding Users File

The users.xml file is located at:
```
<extracted_folder>/users.xml
```

## Running the Extraction Script

Use `uv` to run the extraction script:

```bash
uv run scripts/extract_quiz_to_yaml.py \
  --quiz <path_to_quiz_xml> \
  --users <path_to_users_xml> \
  --output <output_yaml_path>
```

The script is located at `scripts/extract_quiz_to_yaml.py` relative to this skill directory.

The script will output what has been imported to the yaml file. Transmit this to the teacher, so that he can act if anything is suspicious.

It will output the fields that could not be filled from the xml files directly. For those field, try to infer them directly, and ask the users by giving hime the choices you discovered. You can find the course name in the `moodle_backup.xml` file.

## Workflow Summary

1. **Input received** (file or folder path)
2. **Decompress** if .mbz file → temp directory
3. **Find quizzes** → list quiz directories, extract metadata
4. **User selects** quiz(es) to export
5. **Find users.xml** at `<extracted_folder>/users.xml`
6. **Run extraction** for each selected quiz
7. **Cleanup** temp directory if created
8. **Report** output file path(s) to user

## Output

The YAML file will contain:
- Exam name and date
- Questions with max points
- Student responses (mapped to user names)
- Missing fields that need manual completion (reported to user)
