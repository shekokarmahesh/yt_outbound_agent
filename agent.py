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
from livekit.plugins import (groq, silero, noise_cancellation, deepgram, openai)


# load environment variables
load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("ahoum-facilitator-onboarding")
logger.setLevel(logging.INFO)

outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
_default_instructions = (
    "You are Omee, an AI assistant for Ahoum - a spiritual tech platform. Your interface with users will be voice-based phone calls. "
    "You are calling potential facilitators to onboard them to the Ahoum platform. Your goal is to: "
    "1. Introduce yourself and Ahoum briefly "
    "2. Collect basic information from the facilitator (name, spiritual expertise, experience) "
    "3. Provide a short overview of the platform's benefits for facilitators "
    "4. Guide them towards the next steps for joining "
    "Be warm, spiritual, professional, and respectful. Keep conversations concise but meaningful. Allow natural conversation flow."
)


class FacilitatorOnboardingAssistant(BaseAgent):
    """AI assistant Omee for onboarding facilitators to Ahoum spiritual platform"""
    
    def __init__(self):
        super().__init__(instructions=_default_instructions)
    
    @function_tool()
    async def end_call(self):
        """Called when the user wants to end the call"""
        logger.info("User requested to end the call")
        await hangup_call()
        return "Call ended successfully"
    
    @function_tool()
    async def collect_facilitator_info(
        self,
        name: Annotated[str, "The facilitator's full name"],
        expertise: Annotated[str, "Their spiritual/wellness expertise area (e.g. meditation, yoga, reiki, etc.)"],
        experience: Annotated[str, "Years of experience or background in their field"],
    ):
        """Called to collect and store basic information about the potential facilitator"""
        logger.info(f"Collecting info - Name: {name}, Expertise: {expertise}, Experience: {experience}")
        return f"Thank you {name}! I've noted your expertise in {expertise} with {experience} of experience. This aligns perfectly with Ahoum's mission."
    
    @function_tool()
    async def provide_platform_overview(self):
        """Called to give a brief overview of the Ahoum platform benefits for facilitators"""
        logger.info("Providing Ahoum platform overview")
        return json.dumps({
            "platform_benefits": [
                "Reach global audience of spiritual seekers",
                "Flexible scheduling and session management",
                "Secure payment processing",
                "Community of like-minded facilitators",
                "Technology-enhanced spiritual experiences"
            ],
            "message": "Ahoum connects you with seekers worldwide, handles payments, and provides tools for meaningful virtual spiritual sessions. You focus on guiding, we handle the tech."
        })
    
    @function_tool()
    async def schedule_next_steps(
        self,
        contact_method: Annotated[str, "Preferred contact method (email, phone, WhatsApp)"],
        availability: Annotated[str, "When they're available for follow-up"],
    ):
        """Called when facilitator wants to proceed with onboarding"""
        logger.info(f"Scheduling next steps - Contact: {contact_method}, Availability: {availability}")
        return f"Perfect! I'll arrange for our onboarding team to contact you via {contact_method} during {availability}. You'll receive detailed information and can start creating your facilitator profile."
    
    @function_tool()
    async def detected_answering_machine(self):
        """Called when the call reaches voicemail. Use this tool AFTER you hear the voicemail greeting"""
        logger.info("Detected answering machine/voicemail")
        # Leave a brief message and hang up
        ctx = get_job_context()
        if ctx and hasattr(ctx, 'session'):
            await ctx.session.generate_reply(
                instructions="Leave a brief, warm voicemail: 'Hi, this is Omee from Ahoum, a spiritual tech platform. I was calling to discuss facilitator opportunities. I'll try calling back later. Have a blessed day!'"
            )
        await asyncio.sleep(3)  # Allow message to complete
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
    logger.info(f"Calling potential facilitator at {phone_number}")
    
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
    logger.info(f"Participant {participant.identity} joined")    # Create and start the agent session
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
        agent=FacilitatorOnboardingAssistant(),
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
            agent_name="ahoum-facilitator-onboarding",  # Required for explicit dispatch
        )
    )
