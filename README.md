# Cadassist
This AutoCAD Automation Application is a sophisticated tool designed to streamline the process of making real-time changes to AutoCAD projects using natural language commands. This application leverages the power of generative AI, specifically Code-Llama, to generate Python automation scripts based on user inputs. The scripts are executed directly within the AutoCAD environment, allowing users to see their changes reflected in real-time.
# working:
1.Frontend Initialization:
The frontend initializes a Socket.IO connection to the Flask server.

2.Submitting User Input:
When the user submits a command, the frontend sends an HTTP POST request to the Flask server with the user input.

3.Processing Input in the Backend:
The Flask server receives the user input and creates an instance of the Automation class.
The Automation class generates Python automation code using the Ollama LLM model and executes it within the AutoCAD environment.
The backend handles any errors by regenerating the code up to three times.

4.Real-Time Updates:
The backend sends real-time updates to the frontend using Socket.IO.
The frontend listens for these updates and displays the status of the operation to the user.
