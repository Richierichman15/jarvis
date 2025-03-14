"""
Code editor tool for Jarvis.
This tool allows Jarvis to edit, highlight, and execute code.
"""
import os
import sys
import logging
import tempfile
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import pygments
from pygments import lexers, formatters
from pygments.util import ClassNotFound

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodeEditorTool:
    """Tool for editing, highlighting, and executing code."""
    
    def __init__(self):
        """Initialize the code editor tool."""
        self.current_file = None
        self.current_content = None
        self.temp_dir = tempfile.mkdtemp(prefix="jarvis_code_")
        self.history = []  # List of (file, content) tuples to support undo
        
        # Safe directories for executing code
        self.safe_directories = [
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads"),
            os.getcwd(),
            self.temp_dir
        ]
        
        logger.info(f"Initialized code editor with temp directory: {self.temp_dir}")
    
    def _is_path_safe(self, file_path: str) -> bool:
        """Check if the file path is safe to access.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the path is safe, False otherwise
        """
        abs_path = os.path.abspath(os.path.expanduser(file_path))
        
        # Check if path is in safe directories
        for safe_dir in self.safe_directories:
            if abs_path.startswith(safe_dir):
                return True
                
        return False
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read the contents of a file with syntax highlighting.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file content and status information
        """
        try:
            # Check if the path is safe
            if not self._is_path_safe(file_path):
                return {
                    "success": False,
                    "error": f"Access to {file_path} is not allowed for security reasons.",
                    "content": None,
                    "highlighted": None,
                    "file_path": file_path
                }
            
            # Expand user directory if needed
            file_path = os.path.expanduser(file_path)
            
            # Check if file exists
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"File {file_path} does not exist.",
                    "content": None,
                    "highlighted": None,
                    "file_path": file_path
                }
            
            # Check if it's a directory
            if os.path.isdir(file_path):
                return {
                    "success": False,
                    "error": f"{file_path} is a directory, not a file.",
                    "content": None,
                    "highlighted": None,
                    "file_path": file_path
                }
            
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Set as current file
            self.current_file = file_path
            self.current_content = content
            
            # Get syntax highlighting
            highlighted = self._highlight_code(content, file_path)
            
            # Success
            return {
                "success": True,
                "error": None,
                "content": content,
                "highlighted": highlighted,
                "file_path": file_path
            }
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return {
                "success": False,
                "error": f"Error reading file: {str(e)}",
                "content": None,
                "highlighted": None,
                "file_path": file_path
            }
    
    def write_file(self, file_path: str, content: str, create_backup: bool = True) -> Dict[str, Any]:
        """Write content to a file.
        
        Args:
            file_path: Path to the file
            content: Content to write to the file
            create_backup: Whether to create a backup of the original file
            
        Returns:
            Dictionary with status information
        """
        try:
            # Check if the path is safe
            if not self._is_path_safe(file_path):
                return {
                    "success": False,
                    "error": f"Access to {file_path} is not allowed for security reasons.",
                    "file_path": file_path
                }
            
            # Expand user directory if needed
            file_path = os.path.expanduser(file_path)
            
            # Create backup if requested and file exists
            if create_backup and os.path.exists(file_path):
                try:
                    # Save current version in history
                    with open(file_path, 'r', encoding='utf-8') as f:
                        old_content = f.read()
                    
                    # Add to history
                    self.history.append((file_path, old_content))
                    
                    # Limit history size
                    if len(self.history) > 10:
                        self.history.pop(0)
                        
                except Exception as e:
                    logger.warning(f"Could not create backup for {file_path}: {str(e)}")
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Write the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Set as current file
            self.current_file = file_path
            self.current_content = content
            
            # Success
            return {
                "success": True,
                "error": None,
                "file_path": file_path
            }
            
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {str(e)}")
            return {
                "success": False,
                "error": f"Error writing file: {str(e)}",
                "file_path": file_path
            }
    
    def _highlight_code(self, code: str, file_path: Optional[str] = None) -> str:
        """Highlight code for syntax.
        
        Args:
            code: Code to highlight
            file_path: Optional path to help determine the language
            
        Returns:
            Highlighted code as HTML
        """
        try:
            if not code.strip():
                return ""
                
            # Try to guess lexer from file extension
            if file_path:
                try:
                    lexer = lexers.get_lexer_for_filename(file_path)
                except ClassNotFound:
                    # If we can't guess from filename, try to guess from content
                    lexer = lexers.guess_lexer(code)
            else:
                # Guess from content
                lexer = lexers.guess_lexer(code)
                
            # Format with HTML formatter
            formatter = formatters.HtmlFormatter(style='monokai')
            highlighted = pygments.highlight(code, lexer, formatter)
            
            return highlighted
            
        except Exception as e:
            logger.warning(f"Error highlighting code: {str(e)}")
            # Return plain text if highlighting fails
            return f"<pre>{code}</pre>"
    
    def execute_code(self, code: str, language: str) -> Dict[str, Any]:
        """Execute code and return the output.
        
        Args:
            code: Code to execute
            language: Programming language of the code
            
        Returns:
            Dictionary with execution results
        """
        # Map of language identifiers to actual commands
        language_map = {
            "python": "python",
            "python3": "python3",
            "javascript": "node",
            "js": "node",
            "bash": "bash",
            "sh": "sh",
            "ruby": "ruby",
            "perl": "perl",
            "r": "Rscript"
        }
        
        # If language not supported, return error
        if language.lower() not in language_map:
            return {
                "success": False,
                "error": f"Language {language} is not supported for execution.",
                "output": None,
                "language": language
            }
            
        try:
            # Create a temporary file to hold the code
            fd, temp_file = tempfile.mkstemp(suffix=f".{language}", dir=self.temp_dir)
            
            try:
                # Write code to temporary file
                with os.fdopen(fd, 'w') as f:
                    f.write(code)
                
                # Get command to run
                cmd = language_map[language.lower()]
                
                # Execute the code
                process = subprocess.run(
                    [cmd, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=10  # Limit execution time to 10 seconds
                )
                
                # Get output and errors
                stdout = process.stdout
                stderr = process.stderr
                
                return {
                    "success": process.returncode == 0,
                    "error": stderr if process.returncode != 0 else None,
                    "output": stdout,
                    "language": language,
                    "return_code": process.returncode
                }
                
            finally:
                # Clean up the temporary file
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
                    
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Code execution timed out (10 seconds limit).",
                "output": None,
                "language": language
            }
        except Exception as e:
            logger.error(f"Error executing {language} code: {str(e)}")
            return {
                "success": False,
                "error": f"Error executing code: {str(e)}",
                "output": None,
                "language": language
            }
    
    def undo(self) -> Dict[str, Any]:
        """Undo the last file change.
        
        Returns:
            Dictionary with status information
        """
        if not self.history:
            return {
                "success": False,
                "error": "No changes to undo.",
                "file_path": None
            }
            
        # Get the last change
        file_path, content = self.history.pop()
        
        # Write back the previous content
        result = self.write_file(file_path, content, create_backup=False)
        
        if result["success"]:
            result["message"] = f"Successfully reverted changes to {file_path}."
            
        return result
    
    def diff(self, original: str, modified: str) -> str:
        """Calculate the diff between two strings.
        
        Args:
            original: Original text
            modified: Modified text
            
        Returns:
            Diff output
        """
        import difflib
        
        # Create a unified diff
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile="original",
            tofile="modified"
        )
        
        # Join diff lines
        return "".join(diff)
    
    def summarize_results(self, result: Dict[str, Any]) -> str:
        """Summarize the results of a code editor operation.
        
        Args:
            result: Result dictionary from an operation
            
        Returns:
            Formatted string summary
        """
        if "content" in result and result["content"]:
            # This is a read operation with content
            file_path = result.get("file_path", "Unknown file")
            
            summary = f"📄 Code from {file_path}:\n\n```"
            
            # Try to determine language for code fence
            try:
                if file_path:
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext in ['.py', '.pyw']:
                        summary += "python"
                    elif ext in ['.js']:
                        summary += "javascript"
                    elif ext in ['.html']:
                        summary += "html"
                    elif ext in ['.css']:
                        summary += "css"
                    elif ext in ['.sh', '.bash']:
                        summary += "bash"
                    elif ext in ['.md']:
                        summary += "markdown"
                    # Add more languages as needed
            except:
                pass
                
            summary += "\n" + result["content"] + "\n```\n"
            
            return summary
            
        elif "output" in result and result["output"] is not None:
            # This is an execution operation with output
            language = result.get("language", "Unknown")
            success = result.get("success", False)
            output = result.get("output", "")
            error = result.get("error", "")
            
            if success:
                summary = f"✅ Code execution successful ({language}):\n\n```\n{output}\n```\n"
            else:
                summary = f"❌ Code execution failed ({language}):\n\n"
                if error:
                    summary += f"Error:\n```\n{error}\n```\n"
                if output:
                    summary += f"Output:\n```\n{output}\n```\n"
                    
            return summary
            
        else:
            # This is a write/update operation
            success = result.get("success", False)
            error = result.get("error", "")
            file_path = result.get("file_path", "Unknown file")
            message = result.get("message", "")
            
            if success:
                summary = f"✅ File operation successful: {file_path}"
                if message:
                    summary += f"\n{message}"
            else:
                summary = f"❌ File operation failed: {file_path}"
                if error:
                    summary += f"\nError: {error}"
                    
            return summary 