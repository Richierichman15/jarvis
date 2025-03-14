# Jarvis Code Editor

This document explains the code editor functionality integrated into Jarvis AI Assistant.

## Features

The code editor functionality adds the following capabilities to Jarvis:

1. **Code Editing**
   - Edit code files with syntax highlighting
   - Create new files and save them
   - Format and beautify code

2. **Code Execution**
   - Execute code in various programming languages
   - View execution output
   - Handle errors gracefully

3. **Code Analysis**
   - Compare files with diff functionality
   - Get code suggestions from AI
   - Analyze code for improvements

4. **Multiple Language Support**
   - Python
   - JavaScript
   - Bash/Shell
   - Ruby
   - Perl (and more can be easily added)

## Using the Code Editor

### Command Line Interface

Jarvis provides a dedicated code editor mode in the CLI:

```bash
# Start Jarvis in code editor mode
python main.py code

# Start with a specific file
python main.py code path/to/file.py

# Specify a language for execution
python main.py code --language javascript
```

In code editor mode, you can use the following commands:

- `edit filename.py` - Open a file for editing
- `run` - Execute the current code
- `run filename.py` - Execute a specific file
- `save` - Save changes to the current file

You can also ask Jarvis for coding help or suggestions, and it will provide code snippets that you can apply to your files.

### Web Interface

Jarvis also provides a web-based code editor with a split-pane interface:

```bash
# Start the web interface
python main.py --web

# Specify host and port
python main.py --web --host 0.0.0.0 --port 8080

# Customize user name
python main.py --web --name YourName
```

The web interface provides:

- A chat panel for interacting with Jarvis
- A code editor panel with syntax highlighting
- Controls for loading, saving, and executing code
- Execution output display

## Integration with AI

The code editor is fully integrated with Jarvis's AI capabilities, allowing you to:

1. **Get coding assistance**: Ask Jarvis for help with your code, and it will provide suggestions or fixes.

2. **Generate code**: Request Jarvis to generate code for specific tasks, which you can then edit and execute.

3. **Explain code**: Ask Jarvis to explain how a piece of code works.

4. **Optimize code**: Get suggestions for optimizing or refactoring your code.

## Example Usage

### CLI Mode

```
$ python main.py code

JARVIS: Welcome to the code editor mode! You can:
  - Edit a file: 'edit filename.py'
  - Execute code: 'run' or 'run filename.py'
  - Get code suggestions: Just ask a coding question
  - Exit: 'exit' or 'quit'

User (code): edit test.py

JARVIS: 📄 Code from test.py:

```python
def hello():
    print("Hello, world!")
    
hello()
```

User (code): How do I modify this to accept a name parameter?

JARVIS: You can modify the function to accept a name parameter like this:

```python
def hello(name="world"):
    print(f"Hello, {name}!")
    
hello()
hello("Alice")
```

Apply this code? [y/N]: y

Code applied to test.py. Use 'save' to save changes.

User (code): save

✅ File test.py saved successfully.

User (code): run

✅ Code execution successful (python):

Hello, world!
Hello, Alice!
```

### Web Interface

The web interface provides a more interactive experience with a split-pane layout:

- Left panel: Chat with Jarvis
- Right panel: Code editor with execution capabilities

You can chat with Jarvis, get code suggestions, edit code, and execute it all in one interface.

## Implementation Details

The code editor functionality is implemented across several files:

- `jarvis/tools/code_editor.py`: Core implementation of the code editor tool
- `jarvis/cli.py`: CLI interface with code editing mode
- `jarvis/web_interface.py`: Web-based interface with code editing
- `jarvis/tools/tool_manager.py`: Integration with Jarvis's tool system

## Requirements

The code editor functionality requires these additional dependencies:

- `pygments`: For syntax highlighting
- `flask`: For the web interface (only if using the web mode)

These dependencies are included in the requirements.txt file. 