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
get_full_details = {
    "name": "get_full_details",
    "description": "Get the user's full details namely, family details like Person's Religion, Caste Category, Ration card type, and Land Ownership, AND get their work details like Occupation, Nature of Job, and Personal monthly income",
    "parameters": {
        "type": "object",
        "properties": {
            "Religion(CT0000OU)": {
                "type": "string",
                "description": "Get religion of person under Family Details. For example, whether a person is following Hinduism, Islam, Christianity, Buddhism, Jainism, Sikhism, Zoroastrians (Parsis), Not Applicable, Prefer not to say, or Other.",
                "enum": [
                    "Hinduism(CT0000OT)", 
                    "Islam(CT000036)", 
                    "Christianity(CT000039)", 
                    "Buddhism(CT00003A)", 
                    "Jainism(CT00003C)", 
                    "Sikhism(CT000037)", 
                    "Zoroastrians (Parsis)(CT00003B)", 
                    "Not Applicable(CT0001QF)", 
                    "Prefer not to say(CT0005BC)", 
                    "Other(CT00004W)"
                ]
            },
            "Caste Category(CT00003I)": {
                "type": "string",
                "description": "Get caste category of person under Family Details. For example, whether a person belongs to General, SC, ST, OBC, Special Backward Class, Vimukta Jati-A/Denotified tribes-A, Nomadic tribes-B, Nomadic tribes-C, Nomadic tribes-D, or Other.",
                "enum": [
                    "General(LT000001)", 
                    "SC(LT000002)", 
                    "ST(LT000003)", 
                    "OBC(LT000004)", 
                    "Special Backward Class(LT000005)", 
                    "Vimukta Jati-A/Denotified tribes-A(LT000006)", 
                    "Nomadic tribes-B(LT000007)", 
                    "Nomadic tribes-C(LT000008)", 
                    "Nomadic tribes-D(LT000009)", 
                    "Other(LT00000A)"
                ]
            },
            "Ration card type(CT00001D)": {
                "type": "string",
                "description": "Get type of ration card held by the family. For example, whether it is Below Poverty Line, Above Poverty Line, Antyodaya Anna Yojana, State BPL, Annapurna scheme beneficiaries, In process, Not available, Not Applicable, Priority Household, or Other.",
                "enum": [
                    "Below Poverty Line(CT00002D)", 
                    "Above Poverty Line(CT00002C)", 
                    "Antyodaya Anna Yojana(CT0000OH)", 
                    "State BPL(CT000129)", 
                    "Annapurna scheme beneficiaries(CT0001HR)", 
                    "In process(CT0000U6)", 
                    "Not available(CT000068)", 
                    "Not Applicable(CT0001QF)", 
                    "Priority Household(CT0005BF)", 
                    "Other(CT00004W)"
                ]
            },
            "Land Ownership(CT0001AJ)": {
                "type": "string",
                "description": "Get land ownership status under Family Details. For example, whether any family members own land for agriculture, non-agriculture, or do not own any land.",
                "enum": [
                    "Yes - for agriculture(CT0001AH)", 
                    "Yes - for non-agriculture(CT0001AI)", 
                    "No(CT00003K)"
                ]
            },
            "Occupational Status(CT0000PF)": {
                "type": "string",
                "description": "Get the present occupational status of the person. For example, whether they are a Student, Working, Student and Working, Retired, Unemployed, or School Dropout.",
                "enum": [
                    "Student(CT0000P8)", 
                    "Working(CT00019G)", 
                    "Student and Working(CT0001AA)", 
                    "Retired(CT0000PV)", 
                    "Unemployed(CT0000PD)", 
                    "School Dropout(CT0001TY)"
                ]
            },
            "Personal Monthly Income(CT000013)": {
                "type": "number",
                "description": "Get the personal monthly income of the person. Enter the amount in local currency."
            },
            #keyboard option
            "Nature of Job(CT000015)": {
                "type": "string",
                "description": "Get occupation status under Work Details.",
                "enum": [
                    "Anganwadi Helper(CT0001I1)", "Anganwadi worker(CT0001HP)", "Animal Husbandry(CT0001KU)", "Architect(CT0001M0)", "Artisan(CT00019H)", "Auto/Taxi Driver(CT0001H9)", "Beautician(CT0002X2)", "Beedi workers(CT00004U)", "Blacksmith(CT0001NK)", "Bonded Labour(CT0001MW)", "Brick factory worker(CT0001NT)", "Carpenter(CT0001NA)", "Chrome Ore worker(CT0001HM)", "Cine Worker(CT0001BA)", "Coconut tree climber(CT0001PP)", "Coir worker(CT0001PI)", "Construction worker(CT00004R)", "Dairy Farmer(CT00015H)", "Diver(CT0001NJ)", "Dolomite mine worker(CT0001HO)", "Domestic help(CT00004T)", "DTC Employee(CT0001PQ)", "Electrician(CT0001NE)", "Ex-Serviceman of armed forces(CT0001IH)", "Factory Worker(CT0001M5)", "Farm Laborers(CT0000A7)", "Farmer(CT0000BU)", "Fish Sellers(CT00009X)", "Fisherman(CT0001JX)", "Fitter or bar Bender(CT0001NC)", "Flaying(CT00010J)", "Flower Sellers(CT00009Z)", "Fruit Sellers(CT00009Y)", "Garland Sellers(CT0000A0)", "Hammer-smith(CT0001NL)", "Handloom weaver(CT00004S)", "Handicraftsmen/Dastkar(CT000108)", "Iron Ore worker(CT0001HK)", "Iron Smith(CT000127)", "Journalist(CT0001LP)", "Lawyer(CT0001OW)", "Lime industry worker(CT0001NU)", "Leather Industry / Cobbler(CT0001AK)", "Licensed Railway Porters(CT0001H8)", "Limestone mine worker(CT0001HN)", "Manganese Ore worker(CT0001HL)", "Manual scavenging(CT00010M)", "Mason(CT0001N9)", "Mica mine worker(CT0001PN)", "Mine Worker(CT0001BB)", "Mixerman / Sprayman(CT0001NI)", "Own business(CT0000PA)", "Organised Labour(CT0001K7)", "Painter(CT0001NB)", "Papad Rollers(CT0000A2)", "Petty Merchants(CT0000A9)", "Plumber(CT0001ND)", "Poultry farmer(CT0001RE)", "Powerloom worker(CT00019K)", "Professor(CT0001LM)", "Pump Operator(CT0001NM)", "Rag Pickers(CT0000A1)", "Ration Shop Dealer(CT0001LW)", "Railworks Labourer(CT0001NO)", "Roller driver(CT0001NN)", "Rickshaw Drivers(CT0000AA)", "Sale/distribution of illegal liquor(CT00017Q)", "Salt worker(CT00014C)", "Sanitation/Waste collection/Drainage/Manual Scavenging/Waste management etc(CT00019P)", "Scientist(CT0001LN)", "Shop Worker(CT0001M6)", "Small Fabricators(CT0000A8)", "Soil worker(CT0001NS)", "Street vendor(CT00004V)", "Stone Crusher(CT0001LO)", "Stone worker(CT0001NR)", "Tanning(CT00010I)", "Teacher(CT0001JT)", "Toddy tapper(CT0001IQ)", "Tunnel worker(CT0001NQ)", "Vegetable Vendors(CT00009W)", "Waste Picking(CT00010K)", "Waste collection(CT00010L)", "Watchman(CT0001NP)", "Welder(CT0001NG)", "Well digger(CT0001NF)", "Doctor(CT0001RS)", "Tea plantation worker(CT0001RV)", "Tiler (tiles work)(CT0001S6)", "Raj mistry(CT0001S3)", "Roof builder(CT0001S2)", "Mosaic polish(CT0001S4)", "Road builder(CT0001S5)", "Lift builder/stairs builder(CT0001S7)", "Community parks/side walk maker(CT0001S8)", "Establish Modular Units in Kitchen(CT0001S9)", "Accountant/clerk(construction site)(CT0001SA)", "Tailor(CT0001SC)", "Shepherd(CT0001SF)", "Milk vendor(CT0001SE)", "Newspaper hawker(CT0001SD)", "Daily wage Porter(CT0001SH)", "Contractual labour (excluding BOCW and ESI registered workers)(CT0001SG)", "Lorry Driver(CT0001SP)", "Maxi-cab Driver(CT0001SR)", "Bus Driver(CT0001SQ)", "Beggar(CT0001TR)", "Kendu leaf collector(CT0001TS)", "Security guard(CT0001U2)", "Policemen(CT0001TX)", "Sex worker(CT0001TW)", "Washerman/Laundry(CT0001Z4)", "Barber(CT0001Z3)", "Unorganised Worker(CT00030K)", "Contractual Employee(CT0003KN)", "House wife(CT0000PC)", "Artist(CT0005W2)", "Pottery(CT0005WV)", "Basket weaver(CT0005WW)", "Sweeper(CT0005O7)", "Religious priest(CT0005X8)", "Government(CT00005M)", "TV/Internet/Phone Cable Operator(CT0005Z3)", "Vehicle Fleet Operator(CT0005Z9)", "Mechanic(CT0005ZA)", "Delivery Agent(CT0004Q9)", "Rickshaw Puller/Cycle Rickshaw/Hand Rickshaw/Auto(CT0005ZL)", "Goldsmith/Silversmith(CT000605)", "Sculptor(CT000609)", "Armourer/Sword/Shield/Knife/Helmet/Traditional Tool Maker(CT000608)", "Boat Maker(CT000607)", "Locksmith(CT00060B)", "Traditional Doll/Toy Maker(CT00060A)", "Fish Net Maker(CT000606)", "ASHA/ health worker(CT000615)", "Cattle Keeper(CT000622)", "Retired (Government)(CT000629)", "Bee Keepers/Farmers(CT00062W)", "Klin Worker(CT00063C)", "Hamal(CT00063B)", "Gardner(CT00063H)", "Devadasi(CT00063N)", "Fish farm worker/Fish processing centre workers/Crab hunters/owners of boats and traulers/employees of fish seed production centres(CT00063S)", "Sugarcane cutting worker(CT000650)", "Paramilitary(CT000651)", "Armed forces(CT0001UB)", "Neera Collector(CT000657)", "Motor Transport worker(CT00065A)", "Powerloom Weaver(CT00065Z)", "Driver(CT0001JC)", "Small and marginal farmer(CT00066O)"
                ]
            },
            # string dropdown using regex 
            # partial string matching using difflib
        },
        "required": ["Religion(CT0000OU)", "Caste Category(CT00003I)", "Ration card type(CT00001D)", "Land Ownership(CT0001AJ), Occupational Status(CT0000PF),Nature of Job(CT000015), Personal Monthly Income(CT000013)"]
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
                    "function": get_full_details # function_call = {'name': 'get_full_details'},
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