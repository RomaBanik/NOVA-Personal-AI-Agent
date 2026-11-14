
import subprocess
import threading
from pathlib import Path


ERROR_MARKERS = (
    "Traceback (most recent call last):",
    "SyntaxError:",
    "IndentationError:",
    "NameError:",
    "TypeError:",
    "ValueError:",
    "ImportError:",
    "ModuleNotFoundError:",
    "AttributeError:",
    "KeyError:",
    "IndexError:",
    "ZeroDivisionError:",
    "FileNotFoundError:",
    "PermissionError:",
    "RuntimeError:",
)


class ProjectRunner:

    def __init__(self, project_directory):

        self.project_path = Path(project_directory).resolve()

        self.process = None
        self.output = []
        self.all_output = []

        self.lock = threading.Lock()
        self.reader_thread = None

        self.exit_code = None
        self.error_detected = False
        self.error_details = []

    def start(self):

        if not self.project_path.is_dir():
            return {
                "success": False,
                "error": "Project directory not found."
            }

        if not (self.project_path / "main.py").is_file():
            return {
                "success": False,
                "error": "main.py not found."
            }

        if self.process and self.process.poll() is None:
            return {
                "success": False,
                "error": "Project is already running."
            }

        command = [
            "docker", "run", "--rm", "-i",
            "--network", "none",
            "--memory", "256m",
            "--cpus", "0.5",
            "--pids-limit", "64",
            "--read-only",
            "--tmpfs", "/tmp:rw,nosuid,size=32m",
            "--mount",
            f"type=bind,source={self.project_path},target=/app,readonly",
            "--workdir", "/app",
            "-e", "PYTHONUNBUFFERED=1",
            "-e", "TMPDIR=/tmp",
            "-e", "STUDENT_DB_PATH=/tmp/students.db",
            "python:3.12-slim",
            "python", "-u", "main.py"
        ]

        try:

            with self.lock:
                self.output = []
                self.all_output = []
                self.error_detected = False
                self.error_details = []
                self.exit_code = None

            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=0
            )

            self.reader_thread = threading.Thread(
                target=self._read_output,
                daemon=True
            )

            self.reader_thread.start()

            return {
                "success": True,
                "message": "Project started successfully."
            }

        except Exception as exc:

            self.process = None

            return {
                "success": False,
                "error": str(exc)
            }

    def _read_output(self):

        process = self.process

        if process is None:
            return

        try:

            while True:

                # Read available characters without waiting
                # for a complete line from input() prompts.
                character = process.stdout.read(1)

                if character == "":
                    break

                with self.lock:

                    self.output.append(character)
                    self.all_output.append(character)

                    current_text = "".join(self.all_output)

                    if any(
                        marker in current_text
                        for marker in ERROR_MARKERS
                    ):

                        self.error_detected = True

                        if not self.error_details:
                            self.error_details.append(current_text)

        except Exception as exc:

            message = f"\nOutput reader error: {exc}\n"

            with self.lock:

                self.output.append(message)
                self.all_output.append(message)

                self.error_detected = True
                self.error_details.append(message)

        finally:

            exit_code = process.wait()

            with self.lock:

                self.exit_code = exit_code

                if exit_code not in (0, 130):

                    self.error_detected = True

                    if not self.error_details:
                        self.error_details = list(self.all_output)

    def send_input(self, user_input):

        process = self.process

        if process is None or process.poll() is not None:
            return {
                "success": False,
                "error": "Project is not running."
            }

        try:

            with self.lock:

                process.stdin.write(str(user_input) + "\n")
                process.stdin.flush()

            return {
                "success": True,
                "message": "Input sent successfully."
            }

        except Exception as exc:

            return {
                "success": False,
                "error": str(exc)
            }

    def get_output(self):

        with self.lock:

            result = "".join(self.output)
            self.output.clear()

            return result

    def get_status(self):

        process = self.process

        if process is None:
            return {
                "running": False,
                "exit_code": None,
                "error_detected": False,
                "error_details": ""
            }

        current_code = process.poll()

        with self.lock:

            saved_code = self.exit_code
            detected = self.error_detected
            details = "".join(self.error_details)

            if (
                current_code not in (None, 0, 130)
                and not details
            ):

                detected = True
                details = "".join(self.all_output)

        return {
            "running": current_code is None,
            "exit_code": (
                current_code
                if current_code is not None
                else saved_code
            ),
            "error_detected": detected,
            "error_details": details
        }

    def stop(self):

        process = self.process

        if process is None or process.poll() is not None:
            return {
                "success": False,
                "error": "No running project."
            }

        try:

            process.terminate()
            process.wait(timeout=3)

        except subprocess.TimeoutExpired:

            process.kill()
            process.wait()

        except Exception as exc:

            return {
                "success": False,
                "error": str(exc)
            }

        return {
            "success": True,
            "message": "Project stopped successfully."
        }
