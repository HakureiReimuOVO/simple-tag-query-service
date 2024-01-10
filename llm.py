from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain, SequentialChain
from langchain.prompts import PromptTemplate
from connectPGSQL import c2pg
import psycopg2
import codecs
import re

class SQLError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class ParamError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class _prompt():
    """
    rfp_prompt类用于初始化询问过程中的prompt, 其中:
        - `DOMAIN` 表示需要转换成的语言;
        - `DEMAND`为用户的自然语言需求.
    """
    def __init__(self, 
                query_string : dict, 
                host_idx : int = 1) -> None:
        self.host_idx = host_idx
        self.query_string = query_string
        self.statement = None
        self._query_prompt_content_init()
        
    def _query_prompt_content_init(self):
            self.query_prompt_content = '''System: 
Translate the query of user to authoritative, and exactable code ABOUT {DOMAIN} as EXPERTs;
Omit disclaimers, apologies, and AI self-references. Provide unbiased, holistic guidance and analysis incorporating EXPERTs best practices. Elide any comment and interpretation. 

To achieve this task, you need to divide it into two steps:
    1- write PostgreSQL code to query informations in database {DOMAIN};
    2- According to the information database returned, generate your answer. If need, generate a PostgreSQL script to calculate the quantitative conclusion.

The demand of user is following:
Human: {DEMAND}

The table information is following:
<<TABLE INFO>>
table_name: column_name, data_type, character_maximum_length, is_nullable
--------------------------------------------
'''+self._table_prompt+'''
<<TABLE INFO END>>

System: Now you only need to finish step 1, and get more detail to downstream task.
REMEMBER the output PostgreSQL code need to be executable in {DOMAIN}.
Ensure to enclose PostgreSQL statement column names with double quotes like:
<<EXAMPLE>>
SELECT AVG("FuelConsumption")
FROM ship_engine_status;
<<EXAMPLE END>>

Don't do step 2!
AI: '''

    def _code_prompt_content_init(self,):
            self.code_prompt_content = '''System: 
Translate the query of user to authoritative, and exactable code ABOUT {DOMAIN} as EXPERTs;
Omit disclaimers, apologies, and AI self-references. Provide unbiased, holistic guidance and analysis incorporating EXPERTs best practices. Elide any comment and interpretation.
<<INFORMATION>>
'''+self._exec_prompt+'''
<<INFORMATION END>>
System: You need to generate your answer CODE about the {DEMAND} according to the information database returned. 
REMEMBER the output need need to be executable in PostgreSQL. Ensure to enclose PostgreSQL statement column names with double quotes. The answer's format must be MarkDown.
The result except code MUST returned in CHINESE(返回的回答除代码外都必须使用中文!)
'''

    @property
    def query_prompt(self):
        return PromptTemplate(
            input_variables=["DOMAIN", "DEMAND"],
            template=self.query_prompt_content,
        )
    @property
    def code_prompt(self):
        self._code_prompt_content_init()
        return PromptTemplate(
            input_variables=["DEMAND"],
            template=self.code_prompt_content,
        )
    @property
    def _table_prompt(self):
        a = c2pg(self.host_idx)
        __table_prompt = a.table_check()
        if __table_prompt[:8] == "Exception":
            raise SQLError(__table_prompt + ": _prompt._table_prompt") 
        return a.table_check() 
    
    @property
    def _exec_prompt(self, ):
        a = c2pg(self.host_idx)
        if self.statement is None:
            print("statement is none.")
            raise SQLError("Exception: statement is none. : _prompt._exec_promt")
        __query_check = a.query_check(statement=self.statement)
        log = """STATEMENT: 
"""+self.statement+"""
DATABASE RETURN:
"""+str(__query_check)+"\n"
        return log
    
class _chain():
    """
    _chain类用于初始化询问过程中的chain, 其中:
        - `OPENAI_API_KEY`, `OPENAI_API_BASE`为构建llm过程中所需的token, 用于作为访问OPENAI的API
        - `prompt_base`为构建chain过程中所需的prompt, 被封装成了_prompt类.
    在chain中:
        - `translation_chain`负责进行语句转换
    """
    def __init__(self, 
                 OPENAI_API_KEY : str, 
                 OPENAI_API_BASE : str,
                 prompt_base : _prompt,
                 model_name : str = "gpt-3.5-turbo",
                 temperature : float = 0.2) -> None:
        self.prompt_base = prompt_base
        self.llm = ChatOpenAI(model_name=model_name,openai_api_key=OPENAI_API_KEY, openai_api_base=OPENAI_API_BASE, temperature=temperature)
        self.translation_chain = self._chain_generate(prompt=prompt_base.query_prompt, output_key="code_in_database")
        self.seq_chain = SequentialChain(
            chains = [self.translation_chain],
            input_variables=["DOMAIN", "DEMAND"],
            output_variables=["code_in_database",],
            verbose=False,
        )

    def _chain_generate(self, prompt, output_key):
        return LLMChain(
            llm=self.llm,
            prompt=prompt,
            verbose=False,
            output_key=output_key,
        )
    
    def _after_query_(self,):
        self.code_chain = self._chain_generate(prompt=self.prompt_base.code_prompt, output_key="code_in_PostgreSQL")
        self.seq_chain = SequentialChain(
            chains = [self.code_chain],
            input_variables=["DEMAND", "DOMAIN"],
            output_variables=["code_in_PostgreSQL",],
            verbose=True,
        )


class llm_exec():
    @staticmethod
    def process(original_output, pattern = r'```sql(.*?)```'):
        def rev_repr(str : str):
            # return codecs.getdecoder("unicode_escape")(str)[0]
            return str.replace("\\n", "\n")
        matches = re.findall(pattern, repr(original_output))
        matches = [rev_repr(_) for _ in matches]
        # for idx in range(len(matches)):
        #     matches[idx] =  matches[idx][matches[idx].find('\n'):]
        try:
            if pattern == (r'```sql(.*?)```'):
                return matches[0].replace("\n", "").replace("\n", "")
            else:
                return matches[0].strip("'")
        except Exception as e:
            if pattern == r'```sql(.*?)```':
                return llm_exec.process(original_output, r"'(.*?)'")
            else:
                return original_output
        

    @classmethod
    def exec(self, demand_string, domain_string):
        '''
        传入参数"{DEMAND}, {DOMAIN}", 
        将用户的需求(DEMAND)转换成对应数据库(DOMAIN)的代码
        返回大模型的最终答案, 抽取后的代码, 对话完整日志
        '''
        log = ""
        OPENAI_API_KEY = "sk-ElTlBH2nnFK0vsZS35F1C9B2F6254a2f9557A8F749F01eCc"
        OPENAI_API_BASE = "https://api.beer/v1"

        if demand_string is None or domain_string is None:
            raise ParamError("No enough param : llm_exec.exec()")
        

        log += f"DEMEND: {demand_string}, DOMAIN: {domain_string}"
        prompt = _prompt(demand_string)
        chain = _chain(OPENAI_API_KEY, OPENAI_API_BASE, prompt)
        # print(prompt.query_prompt.format(DEMAND=demand_string, DOMAIN=domain_string))
        log += "\nQUERY_PROMPT: \n"+prompt.query_prompt.format(DEMAND=demand_string, DOMAIN=domain_string) + "\n--------------\n"
#         result1 = '''
# ```sql
# -- Step 1: Query the number of suppliers in the 'vendors' table
# SELECT COUNT(*) AS number_of_suppliers FROM vendors;
#     ```'''
        result1 = 'SELECT AVG("FuelConsumption") AS average_carbon_emission\nFROM ship_engine_status'
        # result1 = chain.seq_chain({"DOMAIN":domain_string, "DEMAND":demand_string})["code_in_database"]
        log += "\nQUERY_ANSWER: \n" + result1 + "\n--------------\n"
        prompt.statement = self.process(result1)
        chain._after_query_()
        log += "\nCODE_PROMPT: \n"+prompt.code_prompt.format(DEMAND=demand_string, DOMAIN=domain_string) + "\n--------------\n"
#         result = '''
# 根据查询到的信息，供应商表中共有 7 个供应商。

# 以下是生成一个条形图（bar chart）来可视化显示供应商数量的 Python 代码：

# ```python
# import matplotlib.pyplot as plt

# # 数据
# number_of_suppliers = 7

# # 供应商名称
# supplier_names = ["供应商1", "供应商2", "供应商3", "供应商4", "供应商5", "供应商6", "供应商7"]

# # 创建条形图
# plt.figure(figsize=(10, 6))
# plt.bar(supplier_names, number_of_suppliers, color='blue')
# plt.xlabel("供应商")
# plt.ylabel("供应商数量")
# plt.title("供应商数量统计")
# plt.xticks(rotation=45)
# plt.tight_layout()

# # 显示图表
# plt.show()
# ```

# 这段代码会生成一个简单的条形图，横轴表示不同的供应商，纵轴表示供应商的数量。你可以根据具体需求进一步美化和自定义图表的样式。'''
        result = '```sql\nSELECT AVG("FuelConsumption") AS average_carbon_emission\nFROM ship_engine_status;\n```'
        # result = chain.seq_chain({"DEMAND":demand_string, "DOMAIN":domain_string})["code_in_PostgreSQL"]
        log += "\nCODE_ANSWER: \n" + result + "\n--------------\n"
        a = c2pg(1)
        sqlExecuteResult = a.query_check(self.process(result))
        log += "sqlExecuteResult: \n" + sqlExecuteResult + "\n--------------\n"
        return result, self.process(result), log, sqlExecuteResult
    
if __name__ == "__main__":
    llmAnswer, sqlcode, log, sqlExecuteResult = llm_exec.exec("数据表里有关船引擎的碳排放量平均值是多少", "data_management")
    print(log)