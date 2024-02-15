from .subprocess_language import SubprocessLanguage


class Python(SubprocessLanguage):
    file_extension = "py"
    name = "Python"

    def __init__(self):
        super().__init__()
        self.start_cmd = ["python3", "-iquB"]

    def preprocess_code(self, code):
        """
        Add active line markers
        Wrap in a tryCatch for better error handling in R
        Add end of execution marker
        """

        lines = code.split("\n")
        processed_lines = ['    print("##active_line1##")']

        for line in lines:
            processed_lines.append(f"    {line}")
        # Join lines to form the processed code
        processed_code = "\n".join(processed_lines)

        # Wrap in a tryCatch for error handling and add end of execution marker
        processed_code = f"""try:
{processed_code}
except Exception as e:
    print(f"##execution_error##{{e}}")

print("##end_of_execution##")
"""
        # Count the number of lines of processed_code
        # (R echoes all code back for some reason, but we can skip it if we track this!)
        self.code_line_count = len(processed_code.split("\n")) - 1

        return processed_code

    def detect_active_line(self, line):
        if "##active_line" in line:
            return int(line.split("##active_line")[1].split("##")[0])
        return None

    def detect_end_of_execution(self, line):
        return "##end_of_execution##" in line or "##execution_error##" in line
