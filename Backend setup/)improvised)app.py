from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from pyautocad import Autocad
import logging
from langchain.chains import SimpleSequentialChain
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize AutoCAD
acad = Autocad(create_if_not_exists=True)

# Class to handle automation
class Automation:
    def __init__(self, user_input: str):
        self.user_input = user_input
        self.error = None
        self.counter = 1
        self.curr_response = None
        self.model = OllamaLLM(model="codellama")
        self.exit = False

    def run(self):
        try:
            start = self.curr_response.find("<CODE_START") + 12
            end = self.curr_response.find("<CODE_END")
            code = self.curr_response[start:end]
            exec(code)
        except Exception as error:
            logger.error(f"Error executing code: {error}")
            self.error = str(error)
        else:
            logger.info("Code executed successfully")
            self.error = None

    def execute(self):
        self.generate_code()
        self.run()
        while self.error and self.counter < 4:
            logger.info("Regenerating code...")
            self.generate_code()
            self.run()
        if self.counter >= 4:
            logger.error("Max regeneration attempts reached")
            return "Execution failed. Try again."

    def generate_code(self):
        if self.counter >= 4:
            self.exit = True
        prompt_template = ChatPromptTemplate.from_messages([
            ('system', """You are an assistant to a CAD Designer. Your job is to write a Python function to make real-time changes to a CAD project based on user instructions. 
                        Enclose the code in <CODE_START> and <CODE_END> tags. Also, handle errors gracefully and return an error message if AutoCAD is not running."""),
            ('user', "Write a function to perform the following operation in the currently open CAD model using the `win32com.client` library: {user_input}")
        ])
        if self.counter == 1:
            initial_generate = prompt_template | self.model
            self.curr_response = initial_generate.invoke({'user_input': self.user_input})
        else:
            prompt_template_name = PromptTemplate(
                input_variables=['old_code', 'error', 'user_input'],
                template="""This is the code you generated earlier: {old_code}.
                           This is the error that code generated: {error}.
                           Please fix the error and regenerate the function. Use the original user requirements: {user_input}."""
            )
            regen_code = LLMChain(llm=self.model, prompt=prompt_template_name)
            self.curr_response = regen_code.invoke({'old_code': self.curr_response, 'error': self.error, 'user_input': self.user_input})
        self.counter += 1
        logger.info(f"Code generation attempt {self.counter} complete")

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    user_input = data.get('input')
    logger.info(f"Received input: {user_input}")
    automation_instance = Automation(user_input)
    result = automation_instance.execute()
    success = automation_instance.error is None
    socketio.emit('update', {'success': success, 'code': automation_instance.curr_response})
    return jsonify({'success': success, 'code': automation_instance.curr_response, 'result': result})

@socketio.on('connect')
def test_connect():
    logger.info("Client connected")

@socketio.on('disconnect')
def test_disconnect():
    logger.info("Client disconnected")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
