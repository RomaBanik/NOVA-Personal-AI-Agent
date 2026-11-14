
import json
import re
from pathlib import Path


PROJECTS_ROOT = (
    Path(__file__).resolve().parent.parent / "generated_projects"
)

ALLOWED_EXTENSIONS = {
    ".py",
    ".html",
    ".css",
    ".js",
    ".json",
    ".md",
    ".txt",
    ".sql",
    ".csv",
    ".xml",
    ".yml",
    ".yaml"
}


def safe_name(name):

    cleaned = re.sub(
        r"[^A-Za-z0-9_-]+",
        "",
        str(name or "GeneratedProject")
    )

    return cleaned[:60] or "GeneratedProject"


def extract_json(response_text):

    text = (response_text or "").strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    try:
        return json.loads(text)

    except json.JSONDecodeError:

        start = text.find("{")
        end = text.rfind("}")

        if start >= 0 and end > start:

            return json.loads(
                text[start:end + 1]
            )

        raise ValueError(
            "NOVA did not return valid project JSON."
        )


def generate_project_files(
    client,
    project_description,
    project_name=None,
    model="gemini-3.5-flash-lite"
):

    prompt = f"""
You are NOVA, an expert software developer.

Create a complete working software project
based on the following requirements:

{project_description}

Return ONLY valid JSON in this format:

{{
    "project_name": "ShortProjectName",
    "files": {{
        "main.py": "complete Python source code",
        "README.md": "project instructions"
    }}
}}

IMPORTANT RULES:

1. Include all necessary project files.
2. Include a runnable main.py for Python projects.
3. Use correct and complete code.
4. Avoid unnecessary dependencies.
5. Use relative file paths only.
6. Never use absolute paths.
7. Never use parent-directory traversal.
8. Return valid JSON only.
9. Do not use Markdown code fences.
"""

    response = client.models.generate_content(
        model=model,
        contents=prompt
    )

    data = extract_json(response.text)

    files = data.get("files")

    if not isinstance(files, dict) or not files:

        raise ValueError(
            "Generated response has no valid files."
        )

    return {
        "project_name": safe_name(
            project_name or data.get("project_name")
        ),
        "files": files
    }


def create_project(project_name, files):

    project_name = safe_name(project_name)

    project_dir = PROJECTS_ROOT / project_name

    PROJECTS_ROOT.mkdir(
        parents=True,
        exist_ok=True
    )

    project_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    written_files = []

    for file_name, content in files.items():

        relative_path = Path(str(file_name))

        if (
            relative_path.is_absolute()
            or ".." in relative_path.parts
        ):

            raise ValueError(
                f"Unsafe file path rejected: {file_name}"
            )

        if relative_path.suffix.lower() not in ALLOWED_EXTENSIONS:

            raise ValueError(
                f"File extension not allowed: "
                f"{relative_path.suffix}"
            )

        if not isinstance(content, str):

            raise ValueError(
                f"File content must be text: {file_name}"
            )

        destination = (
            project_dir / relative_path
        ).resolve()

        if project_dir.resolve() not in destination.parents:

            raise ValueError(
                f"Unsafe file path rejected: {file_name}"
            )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        destination.write_text(
            content,
            encoding="utf-8"
        )

        written_files.append(str(relative_path))

    if not (project_dir / "main.py").is_file():

        raise ValueError(
            "Generated project must include main.py."
        )

    return {
        "project_directory": str(project_dir),
        "files": written_files
    }
