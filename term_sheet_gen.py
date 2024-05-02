import os
import json
import re
from ai21 import AI21Client, AI21APIError
from ai21 import errors as ai21_errors
from ai21.models import ChatMessage
import requests
from docx import Document
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ["AI21_API_KEY"]
os.environ["AI21_LOG_LEVEL"] = "DEBUG"

#In order to speed up the answer to the questions, we will call AI21 Contextual Answers in Parallel
def call_ca_parallel(args):
    article, question, category = args
    response = client.answer.create(
        context=article,
        question=question
    )
    answer = response.answer if response.answer else "None"
    return category, answer

def get_answered_questions(user_input, questions):
    answered_questions = {}
    unanswered_questions = {}

    # Use ThreadPoolExecutor to parallelize the calls
    with ThreadPoolExecutor(max_workers=7) as executor:
        # Prepare a list of arguments for the call_ca_parallel function
        future_to_question = {executor.submit(call_ca_parallel, (user_input, q[category], category)): category for q in questions for category in q}

        for future in as_completed(future_to_question):
            # When a future is completed, get the results
            category, answer = future.result()
            if answer != "None":
                answered_questions[category] = answer
            else:
                unanswered_questions[category] = "None"

    return answered_questions, unanswered_questions

def call_jamba(prompt,temperature=.7):

    url = "https://api.ai21.com/studio/v1/chat/completions" # MC - API call 

    payload = {
        "model": "jamba-instruct",
        "messages": [
            {
                "role": "system",
                "content": ""
            },
            {
                "role": "user",
                "content": f'''
        {prompt}
     '''
            }
        ],
        "system": "",
        "max_tokens": 1000,
        "temperature": temperature,
        "top_p": 1,
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    #print(headers)
    response = requests.post(url, json=payload, headers=headers)
    response_json = response.json()
    #print(response_json)
    print(response_json)
    # reply = response_json["choices"][0]["message"]["content"]
    # return(reply)


client = AI21Client(api_key=os.environ["AI21_API_KEY"])

questions=[
    {"Investment Amount":"What is the investment amount being sought by the startup or company?"},
    {"Borrower Name":"What is the name of the borrower or start up?"},
    {"Security Type":"What type of security is being offered to investors?"},
    {"Pre-Money Evaluation":"What is the pre-money valuation of the startup or company?"},
    {"Post-Money Evaluation":"What is the post-money valuation of the startup or company?"},
    {"Percentage Ownership":"What percentage of the company will each investor own after the investment?"},
    {"Anti-Dilution":"What are the terms of the anti-dilution policy?"},
    {"Divident Policy":"What is the company's dividend policy?"},
    {"Redemption Rights":"What redemption rights are available to shareholders?"},
    {"Liquidation Preference":"What are the liquidation preferences specified in the term sheet?"},
    {"Governance Rights":"What governance rights are granted to investors?"},
    {"Information Rights":"What information rights are granted to investors?"},
    {"Transfer Rights":"What are the transfer restrictions on shareholders?"},
    {"Drag-along Rights":"What are the terms of the drag-along rights?"},
    {"First Refusal":"What are the terms for the right of first refusal?"},
    {"Clawback":"What are the clawback terms?"},
    {"Vesting Terms":"What are the vesting terms for equity granted?"},
    {"Business Model":"What is business model of the company seeking the loan?"},
    {"Closing Conditions":"What are the closing conditions for the loan"},
    {"Collateral": "What collateral has the company put up for the loan?"},
    {"Disclaimers":"What disclaimers are mentioned?"},
    
]


raw_notes='''In a negotiation between XYZ Tech Solutions, which provides IT software for financial companies, and ABC Ventures, the focus was on a $2,000,000 equity investment with clear, numerical benchmarks. XYZ Tech, with an EBITDA of $1.2M last year, argued for an $8M pre-money valuation. ABC's investment would shift this to a $10M post-money valuation, granting ABC a 20% stake. The investment terms were sharply defined: Series A Preferred Stock carrying an 8% annual dividend, contingent on XYZ's EBITDA growth of at least 12% per year. As security for a potential loan, XYZ has listed its office buildings and land holdings, which are worth $3,000,000.

The proposed term sheet included a full-ratchet anti-dilution clause to protect ABC against devaluation, governance rights including a board seat and veto power on expenditures over $250,000, and quarterly financial audits to ABC. A five-year redemption clause was agreed upon, allowing ABC to exit with a 12% premium if XYZ's EBITDA grows by 20% within the period. This conversation framed a deal focused on financial health, growth metrics, and strategic alignment, streamlining the partnership terms into a concise, numbers-driven term sheet.'''

answered_questions, unanswered_questions = get_answered_questions(raw_notes, questions)

#keep track of unanswered questions

z=list(unanswered_questions.keys())
for i in range(0,len(z)):
    category=z[i]
    for j in range(0,len(questions)):
        category_2=list(questions[j].keys())[0]
        if category==category_2:
            unanswered_questions[category]=list(questions[j].values())[0]
list_of_unanswered_questions=list(unanswered_questions.values())

# Create a term sheet based on the answered questions
prompt=f'''
You are a lending term-sheet writer. Given input data, you will write a term sheet that clearly fills out each section. The term
sheet should be clear and succinct. Make sure it is has correct punctuation.  Only Generate the term sheet, without any other comments.

An example format is:

Investment Amount: $XXX
Security Type: ABC
Pre-Money Evaluation: $XXX
Post-Money Evaluation: $XXX
Percentage Ownership: XX%
Anti-Dilution: TEXT
Dividend Policy: TEXT
Redemption Rights: TEXT
Governance Rights: TEXT
Information Rights: TEXT
Business Model: TEXT
Collateral: TEXT
____

Here is the raw information:

{answered_questions}

Term Sheet:
'''

print("function call_jamba output next")
print(call_jamba(prompt, temperature=0))

# generated_text=call_jamba(prompt,temperature=0)

# term_sheet=generated_text
# print(term_sheet)

# MC - deductive reasoning after due diligence -- proceed with caution, though I do see ways to do this ourselves with better tech/tools