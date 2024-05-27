from dotenv import load_dotenv
from utils.bhashini_utils import bhashini_translate
from utils.redis_utils import set_redis
import random
from pydub import AudioSegment
import time
import os


load_dotenv(
    dotenv_path="ops/.env",
)

# with open("prompts/prompt.txt", "r") as file:
#     main_prompt = file.read().replace('\n', ' ')

with open("prompts/prompt_v1.txt", "r") as file:
    main_prompt = file.read().replace('\n', ' ')

openai_api_key = os.getenv("OPENAI_API_KEY")
assistant_id = os.getenv("ASSISTANT_ID")
model_name = os.getenv("MODEL_NAME")

#OPENAI FUNCTION CALLS
'''
{
    "firstName": <value>,
    "lastName": <value>,
    "mobile": <value>,
    "gender": <value>,
    "maritalStatus": <value>,
    "dob": <value>,
}
'''   

get_user_details = {
    "name": "get_user_details",
    "description": "Get these user details namely, Person's Name, Mobile Number, Gender, Marital Status, Date of Birth",
    "parameters": {
        "type": "object",
        "properties": {
            "firstName": {
                "type": "string",
                "description": "First Name of Person"
            },
            "lastName": {
                "type": "string",
                "description": "Last Name of Person"
            },
            "mobile": {
                "type": "string", # 'integer'
                "description": "10 digit mobile number. If it has prefix '+91-' at start, then consider mobile number after prefix."
            },
            "gender":{
                "type": "string",
                "description": "Identify gender mentions, recognizing terms for male, female, or other identities. For example, if a person identifies as male, female, or another gender, assign 'M', 'F', or 'O' respectively.",
                "enum": ["M", "F", "O"], # M for Male, F for Female, O for Other
            },
            "maritalStatus": {
                "type": "string",
                "description": "Marital Status of Person. For example, if a person is single, married, divorced, widowed, or other, assign 'Single', 'Married', 'Divorced', 'Widowed', or 'Others' respectively.",
                "enum": ["Single", "Married", "Divorced", "Widowed", "Others"]
            },
            "dob": {
                "type": "string",
                "description": "Date of Birth of Person. Format is YYYY-MM-DD"
            }
        },
        "required": ["firstName", "lastName", "mobile", "gender", "maritalStatus", "dob"]
    }
}

# mini screening questions 
get_family_details = {
    "name": "get_family_details",
    "description": "Get the user's family details namely, Person's Religion, Caste Category, Ration card type, and Land Ownership",
    "parameters": {
        "type": "object",
        "properties": {
            "Religion": {
                "type": "string",
                "description": "Get religion of person. For example, whether a person is following Hinduism, Islam, Christianity, Buddhism, Jainism, Sikhism, Zoroastrians (Parsis), Not Applicable, Prefer not to say, or Other.",
                "enum": ["Hinduism", "Islam", "Christianity", "Buddhism", "Jainism", "Sikhism", "Zoroastrians (Parsis)", "Not Applicable", "Prefer not to say", "Other"]
            },
            "Caste Category": {
                "type": "string",
                "description": "Get caste category of person. For example, whether a person belongs to General, SC, ST, OBC, Special Backward Class, Vimukta Jati-A/Denotified tribes-A, Nomadic tribes-B, Nomadic tribes-C, Nomadic tribes-D, or Other.",
                "enum": ["General", "SC", "ST", "OBC", "SpecialBackwardClass", "VimuktaJati-A/Denotifiedtribes-A", "Nomadictribes-B", "Nomadictribes-C", "Nomadictribes-D", "Other"]
            },
            "Ration card type": {
                "type": "string",
                "description": "Get ration card type. For example, whether a person has Below Poverty Line, Above Poverty Line, Antyodaya Anna Yojana, State BPL, Annapurna scheme beneficiaries, In process, Not available, Not Applicable, Priority Household, or Other ration card.",
                "enum": ["Below Poverty Line", "Above Poverty Line", "Antyodaya Anna Yojana", "State BPL", "Annapurna scheme beneficiaries", "In process", "Not available", "Not Applicable", "Priority Household", "Other"]
            },
            "Land Ownership": {
                "type": "string",
                "description": "Get whether person owns any land. For example, whether a person owns any land under 3 categoeries - agricultural, non-agricultural land or landless.",
                "enum": ["Yes - for agriculture", "Yes - for non agriculture", "No"]
            }
        },
        "required": ["Religion", "Caste Category", "Ration card type", "Land Ownership"]
    }
}

get_work_details = {
    "name": "get_work_details",
    "description": "Get the user's work details namely, Occupation, Nature of Job, and Personal monthly income",
    "parameters": {
        "type": "object",
        "properties": {
            "Occupation": {
                "type": "string",
                "description": "Get present occupational status. For example, whether a person is a Student, Working, Student and Working, Retired, Unemployed, School Dropouts, or has Other status.",
                "enum": ["Student", "Working", "Student and Working", "Retired", "Unemployed", "School Dropouts", "Other"]
            }, #keyboard option
            "Nature of Job": {
                "type": "string",
                "description": "Get person's Nature of Job status. For example, whether a person is a Anganwadi Helper, Blacksmith, Electrician, Scientist, etc.",
                "enum": [
                    "Anganwadi Helper", "Anganwadi worker", "Animal Husbandry", "Architect", "Artisan", "Auto/Taxi Driver",
                    "Beautician", "Beedi workers", "Blacksmith", "Bonded Labour", "Brick factory worker", "Carpenter",
                    "Chrome Ore worker", "Cine Worker", "Coconut tree climber", "Coir worker", "Construction worker",
                    "Dairy Farmer", "Diver", "Dolomite mine worker", "Domestic help", "DTC Employee", "Electrician",
                    "Ex-Serviceman of armed forces", "Factory Worker", "Farm Laborers", "Farmer", "Fish Sellers",
                    "Fisherman", "Fitter or bar Bender", "Flaying", "Flower Sellers", "Fruit Sellers", "Garland Sellers",
                    "Hammer-smith", "Handloom weaver", "Handicraftsmen/Dastkar", "Iron Ore worker", "Iron Smith",
                    "Journalist", "Lawyer", "Lime industry worker", "Leather Industry / Cobbler", "Licensed Railway Porters",
                    "Limestone mine worker", "Manganese Ore worker", "Manual scavenging", "Mason", "Mica mine worker",
                    "Mine Worker", "Matt", "Mixerman / Sprayman", "Own business", "Organised Labour", "Painter",
                    "Papad Rollers", "Petty Merchants", "Plumber", "Poultry farmer", "Powerloom worker", "Professor",
                    "Pump Operator", "Rag Pickers", "Ration Shop Dealer", "Railworks Labourer", "Roller driver",
                    "Rickshaw Drivers", "Sale/distribution of illegal liquor", "Salt worker", "Sanitation/Waste collection/Drainage/Manual Scavenging/Waste management etc",
                    "Scientist", "Shop Worker", "Small Fabricators", "Soil worker", "Street vendor", "Stone Crusher",
                    "Stone worker", "Tanning", "Teacher", "Toddy tapper", "Tunnel worker", "Vegetable Vendors",
                    "Waste Picking", "Waste collection", "Watchman", "Welder", "Well digger", "Doctor", "Tea plantation worker",
                    "Tiler (tiles work)", "Raj mistry", "Roof builder", "Mosaic polish", "Road builder", "Lift builder/stairs builder",
                    "Community parks/side walk maker", "Establish Modular Units in Kitchen", "Accountant/clerk(construction site)",
                    "Tailor", "Shepherd", "Milk vendor", "Newspaper hawker", "Daily wage Porter", "Contractual labour (excluding BOCW and ESI registered workers)",
                    "Lorry Driver", "Maxi-cab Driver", "Bus Driver", "Beggar", "Kendu leaf collector", "Security guard",
                    "Policemen", "Sex worker", "Washerman/Laundry", "Barber", "Unorganised Worker", "Contractual Employee",
                    "House wife", "Artist", "Pottery", "Basket weaver", "Sweeper", "Religious priest", "Government",
                    "TV/Internet/Phone Cable Operator", "Vehicle Fleet Operator", "Mechanic", "Delivery Agent",
                    "Rickshaw Puller/Cycle Rickshaw/Hand Rickshaw/Auto", "Goldsmith/Silversmith", "Sculptor",
                    "Armourer/Sword/Shield/Knife/Helmet/Traditional Tool Maker", "Boat Maker", "Locksmith",
                    "Traditional Doll/Toy Maker", "Fish Net Maker", "ASHA/ health worker", "Cattle Keeper",
                    "Retired (Government)", "Bee Keepers/Farmers", "Klin Worker", "Hamal", "Gardner", "Devadasi",
                    "Fish farm worker/Fish processing centre workers/Crab hunters/owners of boats and traulers/employees of fish seed production centres",
                    "Sugarcane cutting worker", "Paramilitary", "Armed forces", "Neera Collector", "Motor Transport worker",
                    "Powerloom Weaver", "Driver", "Small and marginal farmer", "Other", "Not Applicable", "Not available"
                ]
            }, # string dropdown using regex 
            # partial string matching using difflib
            "Personal monthly income": {
                "type": "integer",
                "description": "Get the personal monthly income of the person."
            }
        },
        "required": ["Occupation", "Nature of Job", "Personal monthly income"]
    }
}

def create_assistant(client, assistant_id):
    try:
        assistant = client.beta.assistants.retrieve(assistant_id=assistant_id)
        return assistant
    except Exception as e:
        # or create a assistant ID in openai playground and use that everytime
        assistant = client.beta.assistants.create(
        name="AI Assistant",
        instructions=main_prompt,
        model=model_name,
        tools=[
                {
                    "type": "function",
                    "function": get_user_details # function_call = {'name': 'get_user_details'},
                },
                {
                    "type": "function",
                    "function": get_family_details # function_call = {'name': 'get_family_details'},
                },
                {
                    "type": "function",
                    "function": get_work_details # function_call = {'name': 'get_work_details'},
                }
                # {
                #     "type": "retrieval",
                #      instructions="You are a customer support chatbot. Use your knowledge base to best respond to customer queries.",
                # }
            ]
        )
        set_redis("assistant_id", assistant.id)
        return assistant

def create_thread(client):
    thread = client.beta.threads.create()
    return thread

def create_run(client, thread_id, assistant_id):
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )
    return run.id, run.status

def upload_message(client, thread_id, input_message, assistant_id):
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=input_message
    )
    run_id, run_status = create_run(client, thread_id, assistant_id)
    return run_id, run_status

def get_run_status(client, thread_id, run_id):
    run = client.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run_id
    )
    delay = 5
    try: 
        run_status = run.status
        print(f"run status inside method is {run_status}")
    except Exception as e:
        return None, None

    while run_status not in ["completed", "failed", "requires_action"]:
        time.sleep(delay)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id,
        )
        run_id = run.id
        run_status = run.status
        delay = 8 if run_status == "requires_action" else 5

    return run_id, run_status

def get_tools_to_call(client, thread_id, run_id):
    run = client.beta.threads.runs.retrieve(
        run_id=run_id,
        thread_id=thread_id
    )
    tools_to_call = run.required_action.submit_tool_outputs.tool_calls
    print(f"tools to call are {tools_to_call}")
    print()
    print(f"run id is {run_id}")
    print()
    print(f"thread id is {thread_id}")
    print()
    if tools_to_call is None:
        print("No tools to call")
    return tools_to_call, run.id, run.status

def get_assistant_message(client, thread_id):
    messages = client.beta.threads.messages.list(
        thread_id=thread_id,
    )
    return messages.data[0].content[0].text.value


def transcribe_audio(audio_file, client):
    transcript = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file
    )
    return transcript.text

def generate_audio(text, client):
    response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
    return response

def get_duration_pydub(file_path):
    try:
        audio_file = AudioSegment.from_file(file_path)
        duration = audio_file.duration_seconds
        return duration
    except Exception as e:
        print(f"Error occurred while getting duration: {e}")
        return None

def get_random_wait_messages(not_always=False, lang="en"):
    messages = [
        "Please wait",
        "I am processing your request",
        "Hold on",
        "I am on it",
        "I am working on it",
    ]
    if not_always:
        rand = random.randint(0, 2)
        if rand == 1:
            random_message = random.choice(messages)
            random_message = bhashini_translate(random_message, "en", lang)
        else:
            random_message = ""
    else:
        random_message = random.choice(messages)
        random_message = bhashini_translate(random_message, "en", lang)
    return random_message
'''
def run_with_streaming_responses(client, thread_id, assistant_id):
    # to add streaming responses
    from typing_extensions import override
    from openai import AssistantEventHandler
    # First, we create a EventHandler class to define
    # how we want to handle the events in the response stream.
    class EventHandler(AssistantEventHandler):    
        @override
        def on_text_created(self, text) -> None:
            print(f"\nassistant > ", end="", flush=True)
            
        @override
        def on_text_delta(self, delta, snapshot):
            print(delta.value, end="", flush=True)
        
        def on_tool_call_created(self, tool_call):
            print(f"\nassistant > {tool_call.type}\n", flush=True)
        
        def on_tool_call_delta(self, delta, snapshot):
            if delta.type == 'code_interpreter':
                if delta.code_interpreter.input:
                    print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)
    # Then, we use the `create_and_stream` SDK helper 
    # with the `EventHandler` class to create the Run 
    # and stream the response.
    with client.beta.threads.runs.create_and_stream(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions="Please address the user as Jane Doe. The user has a premium account.",
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()
'''
# raise_complaint ={
#     "name": "raise_complaint",
#     "description": "Raise complaint",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "description": {
#                 "type": "string",
#                 "description": "Detailed description of complaint"
#             },
#             "service_code": {
#                 "type": "string",
#                 "description": "service code of complaint extracted from description",
#                 "enum": [
#                     "GarbageNeedsTobeCleared", "NoStreetLight", "StreetLightNotWorking",
#                     "BurningOfGarbage", "OverflowingOrBlockedDrain", "illegalDischargeOfSewage",
#                     "BlockOrOverflowingSewage", "ShortageOfWater", "DirtyWaterSupply", "BrokenWaterPipeOrLeakage",
#                     "WaterPressureisVeryLess", "HowToPayPT", "WrongCalculationPT", "ReceiptNotGenerated",
#                     "DamagedRoad", "WaterLoggedRoad", "ManholeCoverMissingOrDamaged", "DamagedOrBlockedFootpath",
#                     "ConstructionMaterialLyingOntheRoad", "RequestSprayingOrFoggingOperation", "StrayAnimals", "DeadAnimals",
#                     "DirtyOrSmellyPublicToilets", "PublicToiletIsDamaged", "NoWaterOrElectricityinPublicToilet", "IllegalShopsOnFootPath",
#                     "IllegalConstructions", "IllegalParking"
#                 ]
#             },
#             "auth_token": {
#                 "type": "string",
#                 "description": "Authentication token of user"
#             },
#             "city": {
#                 "type": "string",
#                 "description": "City of the complaint"
#             },
#             "state": {
#                 "type": "string",
#                 "description": "State of the complaint"
#             },
#             "district": {
#                 "type": "string",
#                 "description": "district of the complaint"
#             },
#             "region": {
#                 "type": "string",
#                 "description": "region of the complaint"
#             },
#             "locality": {
#                 "type": "string",
#                 "description": "locality of the complaint"
#             },
#             "name": {
#                 "type": "string",
#                 "description": "name of the user"
#             },
#             "mobile_number": {
#                 "type": "string",
#                 "description": "mobile number of the user"
#             },
#         },
#         "required": [
#             "description",
#             "service_code",
#             "locality",
#             "city",
#             "name",
#             "mobile_number"
#         ]
#     },
# }