from pydantic import BaseModel  # Data validation aur schema banane ke liye (e.g. user input).
from dotenv import load_dotenv  # .env file se secrets (API key, tokens) load karta hai.
import os, requests, schedule, time, threading, asyncio
# os → Environment variables access karne ke liye.
# requests → WhatsApp API ko HTTP requests bhejne ke liye.
# schedule → Jobs schedule karne ke liye (jaise reminder time set karna).
# time → Sleep aur delay ke liye.
# threading → Background thread mein scheduler chalane ke liye.
# asyncio → Async functions run karne ke liye.
from agents import Agent, OpenAIChatCompletionsModel, AsyncOpenAI, Runner, function_tool, enable_verbose_stdout_logging
from agents.run import RunConfig
# fastapi & cors → API banane ke liye aur CORS allow karne ke liye.
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime


enable_verbose_stdout_logging()

# 🔒 Load env variables
load_dotenv()
OPENAI_API_KEY = os.getenv("API_KEY")
ULTRAMSG_URL = os.getenv("Api_Url")
TOKEN = os.getenv("Token")

if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY is not set")
if not ULTRAMSG_URL or not TOKEN:
    raise ValueError("❌ WhatsApp configuration missing")

# 🚀 FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 📥 User Input Schema
class ReminderInput(BaseModel):
    medicine_name: str
    dose_times: list[str]   # e.g. ["09:00:00", "14:00:00"]
    phone: str


# 📤 WhatsApp Request Schema
class WhatsAppRequest(BaseModel):
    phone: str
    message: str


# 📲 Send WhatsApp Message
def send_whatsapp(data: WhatsAppRequest):
    url = f"{ULTRAMSG_URL}messages/chat"
    payload = f"token={TOKEN}&to={data.phone}&body={data.message}"
    headers = {"content-type": "application/x-www-form-urlencoded"}

    try:
        res = requests.post(
            url,
            data=payload.encode("utf8").decode("iso-8859-1"),
            headers=headers
        )
        if res.status_code == 200:
            print(f"✅ WhatsApp sent: {data.message}")
            return {"status": "✅ WhatsApp message sent!"}
        return {"status": f"❌ Failed: {res.text}"}
    except Exception as e:
        return {"status": f"❌ Error: {str(e)}"}


# 🛠 Tool: Schedule Reminder
@function_tool
def schedule_reminder(phone: str, medicine: str, times: list[str]):
    """
    Schedule WhatsApp reminders for given medicine at specified times.
    """

    def job(phone=phone, medicine=medicine, t=None):
        send_whatsapp(WhatsAppRequest(
            phone=phone,
            message=f"💊 Reminder: It's time to take your medicine '{medicine}' at {t}"
        ))

    # Add jobs in scheduler
    for t in times:
        try:
            # 12-hour format ko 24-hour mein convert karna
            t_24 = datetime.strptime(t.strip(), "%I:%M %p").strftime("%H:%M:%S")
        except:
            # Agar already HH:MM:SS diya hai to same rakho
            t_24 = t

        schedule.every().day.at(t_24).do(job, t=t)
        print(f"⏰ Reminder scheduled at {t_24} (original: {t})")

    return f"✅ Reminders for {medicine} scheduled at {times} for {phone}"


# ✅ Global Scheduler Thread (sirf ek hi dafa chalega)
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Ek hi thread start karna (duplicate threads avoid karne ke liye)
threading.Thread(target=run_schedule, daemon=True).start()


# 🔗 External Client (Gemini)
external_client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

config = RunConfig(
    model=model,
    model_provider=external_client,
    tracing_disabled=False
)

# 🤖 Agent
agent = Agent(
    name="Healthcare Reminder Assistant",
    instructions=(
        "You are a Reminder Assistant. "
        "Take user input about medicine schedules (medicine name, dose times, phone number). "
        "Use the `schedule_reminder` tool to set WhatsApp reminders."
    ),
    model=model,
    tools=[schedule_reminder],
)


# 🚀 FastAPI Endpoint
@app.post("/reminder")
async def create_reminder(details: ReminderInput):
    user_input = f"""
    I need a reminder for my medicine.
    Medicine Name: {details.medicine_name}
    Dose Times: {details.dose_times}
    Phone Number: {details.phone}
    """
    result = await Runner.run(agent, user_input, run_config=config)
    print(f"""response: {result.final_output}, status: Reminders scheduled ✔ """)
    return {"response": result.final_output, "status": "Reminders scheduled ✔ "}


# 🔄 Direct test run
async def main():
    result = await create_reminder(ReminderInput(
        medicine_name="Panadol",
        dose_times=["22:10:00", "22:12:00"],  # apni current time ke hisaab se set karo
        phone="+923481293364"
    ))
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
























# from pydantic import BaseModel  # Data validation aur schema banane ke liye (e.g. user input).
# from dotenv import load_dotenv # .env file se secrets (API key, tokens) load karta hai.
# import os,requests, schedule, time, threading, asyncio
# # os → Environment variables access karne ke liye.
# # requests → WhatsApp API ko HTTP requests bhejne ke liye.
# # schedule → Jobs schedule karne ke liye (jaise reminder time set karna).
# # time → Sleep aur delay ke liye.
# # threading → Background thread mein scheduler chalane ke liye.
# # asyncio → Async functions run karne ke liye.
# from agents import Agent, OpenAIChatCompletionsModel, AsyncOpenAI, Runner, function_tool , enable_verbose_stdout_logging 
# from agents.run import RunConfig
# # fastapi & cors → API banane ke liye aur CORS allow karne ke liye.
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from datetime import datetime


# enable_verbose_stdout_logging()
# # 🔒 Load env variables
# load_dotenv()
# # .env file se API keys read ho rahi hain.
# OPENAI_API_KEY = os.getenv("API_KEY")
# ULTRAMSG_URL = os.getenv("Api_Url")
# TOKEN = os.getenv("Token")

# if not OPENAI_API_KEY:
#     raise ValueError("❌ OPENAI_API_KEY is not set")
# if not ULTRAMSG_URL or not TOKEN:
#     raise ValueError("❌ WhatsApp configuration missing")

# # 🚀 FastAPI app
# app = FastAPI()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )



# # API user se ye 3 input lega:
# # medicine_name
# # dose_times (list of times in "HH:MM:SS")
# # phone (WhatsApp number)

# # 📥 User Input Schema
# class ReminderInput(BaseModel):
#     medicine_name: str
#     dose_times: list[str]   # e.g. ["09:00:00", "14:00:00"]
#     phone: str

# # 📤 WhatsApp Request Schema
# # WhatsApp API ko bhejne ke liye ek schema define kiya.
# class WhatsAppRequest(BaseModel):
#     phone: str
#     message: str

# # 📲 Send WhatsApp Message
# def send_whatsapp(data: WhatsAppRequest):
#     url = f"{ULTRAMSG_URL}messages/chat"
#     payload = f"token={TOKEN}&to={data.phone}&body={data.message}"
#     headers = {"content-type": "application/x-www-form-urlencoded"}



#     try:
#         res = requests.post(
#             url,
#             data=payload.encode("utf8").decode("iso-8859-1"),
#             headers=headers
#         )
#         if res.status_code == 200:
#             print(f"✅ WhatsApp sent: {data.message}")
#             return {"status": "✅ WhatsApp message sent!"}
#         return {"status": f"❌ Failed: {res.text}"}
#     except Exception as e:
#         return {"status": f"❌ Error: {str(e)}"}


# # 🛠 Tool: Schedule Reminder
# @function_tool
# def schedule_reminder(phone: str, medicine: str, times: list[str]):
#     """
#     Schedule WhatsApp reminders for given medicine at specified times.
#     """


# # Ek job function define kiya → jo run hote hi WhatsApp bhejega.
#     def job(phone=phone, medicine=medicine, t=None):
#         send_whatsapp(WhatsAppRequest(
#             phone=phone,
#             message=f"💊 Reminder: It's time to take your medicine '{medicine}' at {t}"
#         ))

#     # Add jobs in schedule
#     # schedule library se har given time pe job run karne ka task add kiya.
#     # for t in times:
#     #     schedule.every().day.at(t).do(job, t=t)

#     for t in times:
#         # Agar user ne 12-hour format diya hai (e.g. 10:30 PM), usko convert karo
#         try:
#             t_24 = datetime.strptime(t.strip(), "%I:%M %p").strftime("%H:%M:%S")
#         except:
#             # Agar already HH:MM:SS diya hai to use hi rakho
#             t_24 = t

#         schedule.every().day.at(t_24).do(job, t=t)
#         print(f"⏰ Reminder scheduled at {t_24} (original: {t})")

#     # Background thread for schedule loop
#     # Background mein infinite loop jo pending jobs run karega.
#     def run_schedule():
#         while True:
#             schedule.run_pending()
#             time.sleep(1)

#     threading.Thread(target=run_schedule, daemon=True).start()
#     return f"✅ Reminders for {medicine} scheduled at {times} for {phone}"

# # Scheduler ko background thread mein chala diya (non-blocking).
# # Confirmation message return kiya.


# # 🔗 External Client (Gemini)
# external_client = AsyncOpenAI(
#     api_key=OPENAI_API_KEY,
#     base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
# )

# model = OpenAIChatCompletionsModel(
#     model="gemini-2.0-flash",
#     openai_client=external_client
# )

# config = RunConfig(
#     model=model,
#     model_provider=external_client,
#     tracing_disabled=False
# )

# # 🤖 Agent
# agent = Agent(
#     name="Healthcare Reminder Assistant",
#     instructions=(
#         "You are a Reminder Assistant. "
#         "Take user input about medicine schedules (medicine name, dose times, phone number). "
#         "Use the `schedule_reminder` tool to set WhatsApp reminders."
#     ),
#     model=model,
#     tools=[schedule_reminder],
# )

# # 🚀 FastAPI Endpoint
# @app.post("/reminder")
# async def create_reminder(details: ReminderInput):
#     user_input = f"""
#     I need a reminder for my medicine.
#     Medicine Name: {details.medicine_name}
#     Dose Times: {details.dose_times}
#     Phone Number: {details.phone}
#     """
#     result = await Runner.run(agent, user_input, run_config=config)
#     print(f"""response: {result.final_output}, status: Reminders scheduled ✔ """)
#     return {"response": result.final_output, "status": "Reminders scheduled ✔ "}


# # 🔄 Direct test run
# async def main():
#     result = await create_reminder(ReminderInput(
#         medicine_name="Panadol",
#         dose_times=["22:02:00", "22:03:00"],  # apni current time ke hisaab se set karo
#         phone="+923481293364"
#     ))
#     print(result)


# if __name__ == "__main__":
#     asyncio.run(main())
