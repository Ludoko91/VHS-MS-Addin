import time
from llama_index.core.tools import FunctionTool
from llama_index.core.agent import ReActAgent
from llama_index.core import PromptTemplate
from llama_index.core import Settings
from llama_index.core.llms import ChatMessage
from llama_index.llms.ollama import Ollama

from tools.db_tools import Simple_tools
from tools.relevant_llm import MQ



model_id = "qwen2.5:14b"
Settings.llm = Ollama(base_url="http://ollama:11434", api_key="token-abc123", model=model_id, request_timeout="60", temperature=0.1, is_function_calling_model=True)
#Settings.llm = Ollama(base_url="http://192.168.178.57:11434",api_key="token-abc123", model=model_id , request_timeout="60",temperature=0.1, is_function_calling_model=True)



#System-Prompts
email_prompt_raw = (
    'You are designed to help with a variety of tasks, from answering questions to providing summaries to other types of analyses.\n\n## Tools\n\nYou have access to a wide variety of tools. You are responsible for using the tools in any sequence you deem appropriate to complete the task at hand.\nThis may require breaking the task into subtasks and using different tools to complete each subtask.\n\nYou have access to the following tools:\n{tool_desc}\n\n\n## Output Format\n\nPlease answer in the same language as the question and use the following format:\n\n```\nThought: The current language of the user is: (user\'s language). I need to use a tool to help me answer the question.\nAction: tool name (one of {tool_names}) if using a tool.\nAction Input: the input to the tool, in a JSON format representing the kwargs (e.g. {{"input": "hello world", "num_beams": 5}})\n```\n\nPlease ALWAYS start with a Thought.\n\nNEVER surround your response with markdown code markers. You may use code markers within your response if you need to.\n\nPlease use a valid JSON format for the Action Input. Do NOT do this {{\'input\': \'hello world\', \'num_beams\': 5}}.\n\nIf this format is used, the tool will respond in the following format:\n\n```\nObservation: tool response\n```\n\nYou should keep repeating the above format till you have enough information to answer the question without using any more tools. At that point, you MUST respond in one of the following two formats:\n\n```\nThought: I can answer without using any more tools. I\'ll use the user\'s language to answer\nAnswer: [your answer here as an email (In the same language as the user\'s question)]\n```\n\n```\nThought: I cannot answer the question with the provided tools.\nAnswer: [your answer here (In the same language as the user\'s question)]\n```\n\n## Current Conversation\n\nBelow is the current conversation consisting of interleaving human and assistant messages.\n'
)
email_prompt_temp = PromptTemplate(email_prompt_raw)
email_prompt = {"agent_worker:system_prompt":email_prompt_temp}

def chatting_func(query,user_database,chat_history=None):

    st = Simple_tools(user_database)
    mq = MQ(user_database)
    #convert mehthod to tool
    course_num_search_tool = FunctionTool.from_defaults(fn= st.course_num_search )
    #course_relevance_tool = FunctionTool.from_defaults(fn= relevant_course_search )
    date_search_tool = FunctionTool.from_defaults(fn= st.date_search )
    #course_keyword_search_tool = FunctionTool.from_defaults(fn= course_keyword_search )
    match_query_with_courses_tool = FunctionTool.from_defaults(fn= mq.match_query_with_courses )


    #call agent with given tool
    agent = ReActAgent.from_tools(tools=[date_search_tool,course_num_search_tool,match_query_with_courses_tool],chat_history=chat_history,verbose=True)
    start_time = time.time()
    response = agent.chat(query)
    print("--- %s seconds ---" % (time.time() - start_time))
    return response

def email_func(query_raw,user_database):

    st = Simple_tools(user_database)
    mq = MQ(user_database)

    #convert mehthod to tool
    course_num_search_tool = FunctionTool.from_defaults(fn= st.course_num_search )
    #course_relevance_tool = FunctionTool.from_defaults(fn= relevant_course_search )
    date_search_tool = FunctionTool.from_defaults(fn= st.date_search )
    #course_keyword_search_tool = FunctionTool.from_defaults(fn= course_keyword_search )
    match_query_with_courses_tool = FunctionTool.from_defaults(fn= mq.match_query_with_courses )

    #call agent with given tool
    agent = ReActAgent.from_tools(tools=[date_search_tool,course_num_search_tool,match_query_with_courses_tool],verbose=True)
    agent.update_prompts(email_prompt)
    start_time = time.time()
    query = f"Schreibe eine Antwort in Form einer Mail auf folgenden Text mithilfe von relvanten Infromationrn, die du von deinen Tools bekommen kannst: {query_raw}"
    response = agent.query(query)
    print("--- %s seconds ---" % (time.time() - start_time))
    return response

def message_conveter(chat_history_messages):
    chat_message_list = []
    x = 1
 
    for chat_message in chat_history_messages:
        #{'sender': 'user', 'message': 'Wann findet ein Schwimmkurs statt?'}
        chat_message = chat_message["message"]
        if chat_message["sender"] == "user":
            message = ChatMessage(role= "user", content= chat_message)
            chat_message_list.append(message)
            x = x + 1
        else:
            message = ChatMessage(role=  "system", content= chat_message)
            chat_message_list.append(message)
            x = x + 1
    
    return chat_message_list


#x =email_func("hallo")
#print(list(x.keys()))