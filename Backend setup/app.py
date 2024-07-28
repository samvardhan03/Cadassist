from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from pyautocad import Autocad, APoint
from langchain.chains import SimpleSequentialChain
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

app = Flask(__name__)
socketio = SocketIO(app)

acad = Autocad(create_if_not_exists=True)

class Automation:
    def __init__(self, user_input: str):
        self.user_input = user_input
        self.error = None
        self.counter = 1
        self.curr_response = None
        self.model = OllamaLLM(model="codellama")
        self.exit = False

    def run(self):
        start = self.curr_response.find("<CODE_START") + 12
        end = self.curr_response.find("<CODE_END")
        code = self.curr_response[start:end]
        try:
            exec(code)
        except Exception as error:
            print("Error detected: ", error)
            self.error = error
        else:
            print("No errors")
            self.error = None
        finally:
            print(".run() method complete!")

    def execute(self):
        self.generate_code()
        self.run()
        while self.error is not None:
            print("Regenerating....")
            self.generate_code()
            if self.exit:
                return "Execution failed. Try again."
            self.run()
        print(".execute() method complete!")

    def generate_code(self):
        if self.counter >= 4:
            self.exit = True
        elif self.counter == 1:
            prompt_template = ChatPromptTemplate.from_messages([
                ('system', """You are an assistant to a CAD Designer. Your job is to write a Python function to make real-time changes to a CAD project based on user instructions. 
                            Enclose the code in <CODE_START> and <CODE_END> tags. Also, handle errors gracefully and return an error message if AutoCAD is not running."""),
                ('user', "Write a function to perform the following operation in the currently open CAD model using the `win32com.client` library: {user_input}")
            ])
            response = prompt_template | self.model
            self.curr_response = response.invoke({'user_input': self.user_input})
            self.counter += 1
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
#instance of the automation class and for real time updates
@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    user_input = data.get('input')
    automation_instance = Automation(user_input)
    automation_instance.execute()
    success = automation_instance.error is None
    socketio.emit('update', {'success': success, 'code': automation_instance.curr_response})
    return jsonify({'success': success, 'code': automation_instance.curr_response})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
