"""
File operations tool for Jarvis.
This tool allows Jarvis to read and write files.
"""
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileOperations:
    """File operations tool for reading and writing files."""
    
    def __init__(self, max_file_size: int = 1024 * 1024):
        """Initialize the file operations tool.
        
        Args:
            max_file_size: Maximum file size to read (in bytes)
        """
        self.max_file_size = max_file_size
        self.safe_directories = [
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads"),
            os.getcwd()
        ]
    
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
        """Read the contents of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with status and content/error
        """
        if not self._is_path_safe(file_path):
            error_msg = f"Security error: Cannot access file outside safe directories: {file_path}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
        try:
            file_path = os.path.expanduser(file_path)
            if not os.path.exists(file_path):
                error_msg = f"File not found: {file_path}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                error_msg = f"File too large: {file_size} bytes (max: {self.max_file_size} bytes)"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            logger.info(f"Successfully read file: {file_path}")
            return {
                "success": True, 
                "content": content,
                "size": file_size,
                "path": file_path
            }
                
        except Exception as e:
            error_msg = f"Error reading file {file_path}: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def write_file(self, file_path: str, content: str, append: bool = False) -> Dict[str, Any]:
        """Write content to a file.
        
        Args:
            file_path: Path to the file
            content: Content to write
            append: If True, append to the file, otherwise overwrite
            
        Returns:
            Dictionary with status and error message if any
        """
        if not self._is_path_safe(file_path):
            error_msg = f"Security error: Cannot write to file outside safe directories: {file_path}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
        try:
            file_path = os.path.expanduser(file_path)
            
            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                
            # Write to file
            mode = 'a' if append else 'w'
            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"Successfully {'appended to' if append else 'wrote'} file: {file_path}")
            return {
                "success": True,
                "path": file_path,
                "size": len(content),
                "mode": "append" if append else "write"
            }
                
        except Exception as e:
            error_msg = f"Error writing to file {file_path}: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def list_directory(self, directory_path: str) -> Dict[str, Any]:
        """List contents of a directory.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            Dictionary with status and file list/error
        """
        if not self._is_path_safe(directory_path):
            error_msg = f"Security error: Cannot list directory outside safe directories: {directory_path}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
        try:
            directory_path = os.path.expanduser(directory_path)
            if not os.path.exists(directory_path):
                error_msg = f"Directory not found: {directory_path}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
            if not os.path.isdir(directory_path):
                error_msg = f"Not a directory: {directory_path}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
            files = []
            directories = []
            
            # List directory contents
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                if os.path.isdir(item_path):
                    directories.append(item)
                else:
                    files.append(item)
                    
            logger.info(f"Successfully listed directory: {directory_path}")
            return {
                "success": True,
                "path": directory_path,
                "files": files,
                "directories": directories,
                "total_items": len(files) + len(directories)
            }
                
        except Exception as e:
            error_msg = f"Error listing directory {directory_path}: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
    def summarize_results(self, result: Dict[str, Any]) -> str:
        """Summarize operation results into a readable format.
        
        Args:
            result: Operation result dictionary
            
        Returns:
            Formatted summary string
        """
        if not result.get("success", False):
            return f"File Operation Error: {result.get('error', 'Unknown error')}"
            
        operation_type = None
        
        if "content" in result:
            # Read operation
            operation_type = "read"
            summary = f"File Read: {result['path']}\n"
            summary += f"Size: {result['size']} bytes\n\n"
            summary += "Content:\n"
            
            # If content is very large, truncate it
            content = result['content']
            if len(content) > 1000:
                content = content[:1000] + "\n... [Content truncated, too large to display fully]"
                
            summary += content
            
        elif "files" in result:
            # List directory operation
            operation_type = "list"
            summary = f"Directory Listing: {result['path']}\n"
            summary += f"Total Items: {result['total_items']}\n\n"
            
            if result['directories']:
                summary += "Directories:\n"
                for directory in sorted(result['directories']):
                    summary += f"- {directory}/\n"
                    
            if result['files']:
                summary += "\nFiles:\n"
                for file in sorted(result['files']):
                    summary += f"- {file}\n"
                    
        else:
            # Write operation
            operation_type = "write"
            summary = f"File {result['mode'].capitalize()} Operation: {result['path']}\n"
            summary += f"Wrote {result['size']} bytes\n"
            summary += "Operation successful."
            
        logger.info(f"Summarized {operation_type} operation for {result.get('path', 'unknown path')}")
        return summary 