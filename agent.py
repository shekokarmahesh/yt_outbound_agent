import asyncio
import logging
from dotenv import load_dotenv
import json
import os
from time import perf_counter
from typing import Annotated
from livekit import rtc, api
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
    AgentSession,
    Agent as BaseAgent,
    get_job_context,
    function_tool,
)
from livekit.plugins import deepgram, openai, silero


# load environment variables
load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("outbound-caller")
logger.setLevel(logging.INFO)

outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
_default_instructions = (
    "You are a scheduling assistant for a game development studio. Your interface with user will be voice. "
    "You will be on a call with a customer who has an upcoming appointment. Your goal is to confirm the appointment details. "
    "As a customer service representative, you will be polite and professional at all times. Allow user to end the conversation."
)


class SchedulingAssistant(BaseAgent):
    """Scheduling assistant agent with function tools"""
    
    def __init__(self):
        super().__init__(instructions=_default_instructions)
    
    @function_tool()
    async def end_call(self):
        """Called when the user wants to end the call"""
        logger.info("User requested to end the call")
        await hangup_call()
        return "Call ended successfully"
    
    @function_tool()
    async def look_up_availability(
        self,
        date: Annotated[str, "The date of the appointment to check availability for"],
    ):
        """Called when the user asks about alternative appointment availability"""
        logger.info(f"Looking up availability for {date}")
        await asyncio.sleep(1)  # Simulate lookup
        return json.dumps({
            "available_times": ["1pm", "2pm", "3pm"],
            "message": f"Available appointment slots for {date}: 1pm, 2pm, 3pm"
        })
    
    @function_tool()
    async def confirm_appointment(
        self,
        date: Annotated[str, "date of the appointment"],
        time: Annotated[str, "time of the appointment"],
    ):
        """Called when the user confirms their appointment on a specific date. Use this tool only when they are certain about the date and time."""
        logger.info(f"Confirming appointment for {date} at {time}")
        return f"Appointment confirmed for {date} at {time}. Thank you!"
    
    @function_tool()
    async def detected_answering_machine(self):
        """Called when the call reaches voicemail. Use this tool AFTER you hear the voicemail greeting"""
        logger.info("Detected answering machine/voicemail")
        # Leave a brief message and hang up
        ctx = get_job_context()
        if ctx and hasattr(ctx, 'session'):
            await ctx.session.generate_reply(
                instructions="Leave a brief voicemail message saying you'll call back later, then end the call."
            )
        await asyncio.sleep(2)  # Allow message to complete
        await hangup_call()
        return "Voicemail message left"


async def hangup_call():
    """Utility function to hang up the call"""
    ctx = get_job_context()
    if ctx is None:
        logger.warning("No job context available for hangup")
        return
    
    try:
        await ctx.api.room.delete_room(
            api.DeleteRoomRequest(room=ctx.room.name)
        )
        logger.info("Call ended - room deleted")
    except Exception as e:
        logger.warning(f"Error hanging up call: {e}")


async def entrypoint(ctx: JobContext):
    """Entry point for the outbound caller agent"""
    global outbound_trunk_id
    
    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Get phone number from job metadata
    phone_number = ctx.job.metadata
    logger.info(f"Dialing {phone_number}")
    
    user_identity = "phone_user"
    
    # Create the SIP participant (starts dialing)
    try:
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=outbound_trunk_id,
                sip_call_to=phone_number,
                participant_identity=user_identity,
                wait_until_answered=True,  # Wait for the call to be answered
            )
        )
        logger.info("SIP participant created successfully")
    except api.TwirpError as e:
        logger.error(f"Error creating SIP participant: {e.message}, "
                    f"SIP status: {e.metadata.get('sip_status_code')} "
                    f"{e.metadata.get('sip_status')}")
        ctx.shutdown()
        return

    # Wait for participant to join
    participant = await ctx.wait_for_participant(identity=user_identity)
    logger.info(f"Participant {participant.identity} joined")

    # Create and start the agent session
    session = AgentSession(
        stt=deepgram.STT(model="nova-2-phonecall"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(),
        vad=silero.VAD.load(),
    )
      # Store session in context for potential access by tools
    ctx.session = session
    
    # Start the session
    await session.start(
        room=ctx.room,
        agent=SchedulingAssistant(),
    )
    
    # Monitor call status
    start_time = perf_counter()
    call_answered = False
    
    while perf_counter() - start_time < 60:  # 60 second timeout
        call_status = participant.attributes.get("sip.callStatus")
        
        if call_status == "active" and not call_answered:
            logger.info("Call answered - user picked up")
            call_answered = True
            
            # Wait a moment for the call to stabilize before generating reply
            await asyncio.sleep(1)
            
            # Don't greet immediately for outbound calls - wait for user to speak first
            # The agent will respond when the user talks
            break
            
        elif call_status == "automation":
            # DTMF dialing state
            logger.info("Call in automation state (DTMF)")
            
        elif participant.disconnect_reason == rtc.DisconnectReason.USER_REJECTED:
            logger.info("User rejected the call")
            break
            
        elif participant.disconnect_reason == rtc.DisconnectReason.USER_UNAVAILABLE:
            logger.info("User did not pick up")
            break
            
        await asyncio.sleep(0.5)
    
    if not call_answered:
        logger.info("Call timed out or was not answered")
        ctx.shutdown()


if __name__ == "__main__":
    if not outbound_trunk_id or not outbound_trunk_id.startswith("ST_"):
        raise ValueError("SIP_OUTBOUND_TRUNK_ID is not set or invalid")
    
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="outbound-caller",  # Required for explicit dispatch
        )
    )
