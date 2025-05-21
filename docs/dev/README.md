Here is a guide for developers for build the AutoData package.

Let's first talk about the core workflow of the package. 

At the center of the AutoData is a multi-agent system that contains agents divided into two groups, i.e., research group and development group, supervised by a manager agent.
Specificaly, the research group contains four agents, i.e., planner agent, web agent, tool agent, and blueprint agent. 
Each agent in the research group is equipped a unique prompt template (see [prompts](../prompts/)). 
For planner agent, it is responsible for planning the research process, including breakdown the user instruction into a series of subtasks, and for each subtask, selecting one agent to execute it. 
For web agent, it use python package "Browser-use" to browse the web and extract the knowledge for programming. Note here, only knowledge for programming is extracted. 
For tool agent, it is responsible for using tools such as google search to find the information needed for the research. 

Afterward, blueprint agent will generate a development blueprint based on the research result.
Here the research result is about how to build a python script that can be used to automate the data collection process that the output data is align with user instructions.

In the other side, i.e., development group, it contains a engineer to build the python script based on the development blueprint, and a test agent to debug and test the python script. 
One additional agent, validation agent to validate the output data. 

Next, lets talk about the framework package to use. 
use LangChain and LangGraph as the framework to build the multi-agent system. 
Besides, I want to design a customized collaboration tool binding into the message interface of LangGraph.


For LLMs output, use pydantic to parse the output into a structured format. 